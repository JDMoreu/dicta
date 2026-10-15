# -*- coding: utf-8 -*-
"""dicta_capture.py - WASAPI *process loopback* capture for Windows.

Capture the audio rendered by ONE process (optionally its whole process tree)
with the Windows process-loopback API (Windows 10 build 20348+ / Windows 11).

Self contained: ``ctypes`` + stdlib + ``numpy`` only.  No ``comtypes``, no
``pywin32``.  The module imports cleanly on ANY OS; only :func:`list_audio_apps`
and :meth:`ProcessLoopbackCapture.start` raise ``RuntimeError`` off Windows.

Public API
----------
``list_audio_apps() -> list[dict]``
    Audio sessions of the default *render* endpoint.  Each item::

        {"pid": int, "name": str, "exe": str, "playing": bool}

    Sorted with the currently-playing sessions first.

``class ProcessLoopbackCapture(pid, samplerate=48000, channels=2,
                               blocksize=1024, include_tree=True)``

    ``start() -> bool``
    ``read(timeout=0.5) -> numpy.ndarray | None``   float32, (frames, channels)
    ``stop() -> None``
    ``error -> str``

The output is interleaved float32 with scale ``1.0`` == full scale, which is
exactly the shape the rest of *dicta* expects.

Notes / gotchas handled
-----------------------
* ``ActivateAudioInterfaceAsync`` with the *virtual* device
  ``VAD\\Process_Loopback`` and a ``VT_BLOB`` ``PROPVARIANT`` holding an
  ``AUDIOCLIENT_ACTIVATION_PARAMS`` (``ActivationType == 1``).
* A hand written ``IActivateAudioInterfaceCompletionHandler`` that waits (up to
  5 s) for ``ActivateCompleted``.
* Every Windows function has ``argtypes``/``restype`` declared and every HANDLE
  is a 64-bit pointer type (the classic 32-bit ``HANDLE`` truncation bug).
* ``Initialize`` uses the mix format from ``GetMixFormat`` as-is (process
  loopback requires it), with a plain ``WAVEFORMATEX`` fallback.
* ``AUDCLNT_E_BUFFER_SIZE_NOT_ALIGNED`` triggers a re-init using
  ``GetDevicePeriod``.
* ``GetNextPacketSize`` / ``GetBuffer`` / ``ReleaseBuffer`` loop honouring
  ``AUDCLNT_BUFFERFLAGS_SILENT`` and counting
  ``AUDCLNT_BUFFERFLAGS_DATA_DISCONTINUITY``.
* ``stop()`` always releases everything (Stop, release capture client, release
  audio client, CloseHandle, CoUninitialize).
"""

from __future__ import annotations

import sys
import threading
import time
from typing import Dict, List, Optional

import numpy as np

__all__ = ["list_audio_apps", "ProcessLoopbackCapture", "CaptureError"]

IS_WINDOWS = sys.platform == "win32"


class CaptureError(RuntimeError):
    """Raised for recoverable/known capture problems."""


def _s32(v: int) -> int:
    """Reinterpret a 32-bit value as a signed int (HRESULT semantics)."""
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


# --- HRESULTs -------------------------------------------------------------
S_OK = 0
E_NOINTERFACE = _s32(0x80004002)
RPC_E_CHANGED_MODE = _s32(0x80010106)

AUDCLNT_S_BUFFER_EMPTY = 0x08890001
AUDCLNT_E_UNSUPPORTED_FORMAT = _s32(0x88890008)
AUDCLNT_E_BUFFER_SIZE_NOT_ALIGNED = _s32(0x88890019)

# --- stream flags / modes -------------------------------------------------
AUDCLNT_SHAREMODE_SHARED = 0
AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000
AUDCLNT_STREAMFLAGS_EVENTCALLBACK = 0x00040000
AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM = 0x80000000

AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK = 1
AUDCLIENT_PROCESS_LOOPBACK_MODE_INCLUDE_TREE = 0
AUDCLIENT_PROCESS_LOOPBACK_MODE_EXCLUDE_TREE = 1

AUDCLNT_BUFFERFLAGS_DATA_DISCONTINUITY = 0x00000001
AUDCLNT_BUFFERFLAGS_SILENT = 0x00000002

COINIT_MULTITHREADED = 0x2
COINIT_APARTMENTTHREADED = 0x0
CLSCTX_ALL = 0x17
VT_BLOB = 65
VT_LPWSTR = 31

WAVE_FORMAT_PCM = 1
WAVE_FORMAT_IEEE_FLOAT = 3
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

DEVICE_NAME_PROCESS_LOOPBACK = "VAD\\Process_Loopback"

WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 0x102


if IS_WINDOWS:  # pragma: no cover - platform specific
    import ctypes
    from ctypes import wintypes

    _ole32 = ctypes.WinDLL("ole32")
    _mmdev = ctypes.WinDLL("Mmdevapi.dll")
    _kernel32 = ctypes.WinDLL("kernel32")

    HRESULT = ctypes.c_long
    DWORD = wintypes.DWORD
    HANDLE = wintypes.HANDLE

    # ---------------------------------------------------------------- GUIDs
    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_ubyte * 8),
        ]

        def __init__(self, spec=None):
            super().__init__()
            if spec:
                self.set(spec)

        def set(self, spec: str) -> None:
            s = spec.strip().strip("{}")
            a, b, c, d, e = s.split("-")
            self.Data1 = int(a, 16)
            self.Data2 = int(b, 16)
            self.Data3 = int(c, 16)
            rest = d + e
            for i in range(8):
                self.Data4[i] = int(rest[2 * i:2 * i + 2], 16)

        def __eq__(self, other):  # type: ignore[override]
            try:
                return bytes(self) == bytes(other)
            except TypeError:
                return NotImplemented

        def __hash__(self):  # type: ignore[override]
            return hash(bytes(self))

    def _guid(spec: str) -> "GUID":
        return GUID(spec)

    IID_IUnknown = _guid("00000000-0000-0000-C000-000000000046")
    IID_IAudioClient = _guid("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2")
    IID_IAudioCaptureClient = _guid("C8ADBD64-E71E-48A0-A4DE-185C395CD317")
    IID_IActivateAudioInterfaceCompletionHandler = _guid(
        "41D949AB-9862-444A-80F6-C261334DA5EB")
    # On current Windows builds ActivateAudioInterfaceAsync queries the
    # completion handler for this IID (observed on build 26300); accept it too.
    IID_IActivateAudioInterfaceCompletionHandler_ALT = _guid(
        "94EA2B94-E9CC-49E0-C0FF-EE64CA8F5B90")
    IID_IActivateAudioInterfaceAsyncOperation = _guid(
        "72A22D78-CDE4-431D-B8CC-843A71199B6D")
    IID_IMMDeviceEnumerator = _guid("A95664D2-9614-4F35-A746-DE8DB63617E6")
    IID_IAudioSessionManager2 = _guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F")
    IID_IAudioSessionEnumerator = _guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8")
    IID_IAudioSessionControl2 = _guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D")
    IID_IPropertyStore = _guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")
    CLSID_MMDeviceEnumerator = _guid("BCDE0395-E52F-467C-8E3D-C4579291692E")

    # PKEY_SYSTEM_NAME = {B3F8FA53-0004-438E-9003-51A46E139BFC}, 6
    # (the audio-session friendly name; NOT the loopback device id)
    FMTID_SYSTEM_NAME = _guid("B3F8FA53-0004-438E-9003-51A46E139BFC")
    PID_SYSTEM_NAME = 6

    KSDATAFORMAT_SUBTYPE_IEEE_FLOAT = _guid("00000003-0000-0010-8000-00AA00389B71")
    KSDATAFORMAT_SUBTYPE_PCM = _guid("00000001-0000-0010-8000-00AA00389B71")

    # ------------------------------------------------------------ structures
    class WAVEFORMATEX(ctypes.Structure):
        _pack_ = 1
        _fields_ = [
            ("wFormatTag", ctypes.c_uint16),
            ("nChannels", ctypes.c_uint16),
            ("nSamplesPerSec", ctypes.c_uint32),
            ("nAvgBytesPerSec", ctypes.c_uint32),
            ("nBlockAlign", ctypes.c_uint16),
            ("wBitsPerSample", ctypes.c_uint16),
            ("cbSize", ctypes.c_uint16),
        ]

    class BLOB(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("pBlobData", ctypes.POINTER(ctypes.c_ubyte)),
        ]

    class _PV_UNION(ctypes.Union):
        _fields_ = [
            ("blob", BLOB),
            ("pwszVal", wintypes.LPWSTR),
            ("ulVal", ctypes.c_ulong),
            ("uhVal", ctypes.c_ulonglong),
            ("_pad", ctypes.c_ubyte * 16),
        ]

    class PROPVARIANT(ctypes.Structure):
        _fields_ = [
            ("vt", ctypes.c_uint16),
            ("wReserved1", ctypes.c_uint16),
            ("wReserved2", ctypes.c_uint16),
            ("wReserved3", ctypes.c_uint16),
            ("u", _PV_UNION),
        ]

    class PROPERTYKEY(ctypes.Structure):
        _fields_ = [("fmtid", GUID), ("pid", ctypes.c_ulong)]

    class AUDIOCLIENT_PROCESS_LOOPBACK_PARAMS(ctypes.Structure):
        _fields_ = [
            ("TargetProcessId", ctypes.c_ulong),
            ("ProcessLoopbackMode", ctypes.c_int),
        ]

    class AUDIOCLIENT_ACTIVATION_PARAMS(ctypes.Structure):
        _fields_ = [
            ("ActivationType", ctypes.c_int),
            ("ProcessLoopbackParams", AUDIOCLIENT_PROCESS_LOOPBACK_PARAMS),
        ]

    # ------------------------------------------------------------ prototypes
    _ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    _ole32.CoInitializeEx.restype = ctypes.c_long
    _ole32.CoUninitialize.argtypes = []
    _ole32.CoUninitialize.restype = None
    _ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(GUID), ctypes.c_void_p, ctypes.c_ulong,
        ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
    _ole32.CoCreateInstance.restype = ctypes.c_long
    _ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    _ole32.CoTaskMemFree.restype = None
    _ole32.CoTaskMemAlloc.argtypes = [ctypes.c_size_t]
    _ole32.CoTaskMemAlloc.restype = ctypes.c_void_p

    _mmdev.ActivateAudioInterfaceAsync.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(GUID),
        ctypes.POINTER(PROPVARIANT),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    _mmdev.ActivateAudioInterfaceAsync.restype = ctypes.c_long

    _kernel32.CreateEventW.argtypes = [
        ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    _kernel32.CreateEventW.restype = HANDLE
    _kernel32.CloseHandle.argtypes = [HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.WaitForSingleObject.argtypes = [HANDLE, ctypes.c_ulong]
    _kernel32.WaitForSingleObject.restype = ctypes.c_ulong
    _kernel32.OpenProcess.argtypes = [ctypes.c_ulong, wintypes.BOOL, ctypes.c_ulong]
    _kernel32.OpenProcess.restype = HANDLE
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        HANDLE, ctypes.c_ulong, wintypes.LPWSTR, ctypes.POINTER(ctypes.c_ulong)]
    _kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

    _ole32.PropVariantClear.argtypes = [ctypes.POINTER(PROPVARIANT)]
    _ole32.PropVariantClear.restype = ctypes.c_long

    # --------------------------------------------------- COM vtable helpers
    def _as_ptr(v):
        return v if isinstance(v, ctypes.c_void_p) else ctypes.c_void_p(v)

    def _vtbl_call(ptr, index, restype, argtypes, *args):
        p = _as_ptr(ptr)
        table = ctypes.cast(
            p, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        proto = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
        fn = proto(table[index])
        return fn(p, *args)

    def _release(ptr):
        if ptr:
            try:
                _vtbl_call(ptr, 2, ctypes.c_ulong, [])
            except Exception:
                pass

    def _hr_ok(hr: int) -> bool:
        return hr >= 0

    # --------------------------------------- completion handler (IActivate..)
    _HANDLERS: Dict[int, "object"] = {}
    _HANDLERS_LOCK = threading.Lock()
    # Every handler ever created is kept alive for the process lifetime: Windows
    # may still invoke ActivateCompleted (or Release) on a worker thread after
    # start() returns, and letting ctypes free the vtable would crash the host.
    _ALL_HANDLERS: List["object"] = []

    _QI_FN = ctypes.WINFUNCTYPE(
        ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p))
    _REF_FN = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
    _DONE_FN = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)

    class _HandlerVtbl(ctypes.Structure):
        _fields_ = [
            ("QueryInterface", _QI_FN),
            ("AddRef", _REF_FN),
            ("Release", _REF_FN),
            ("ActivateCompleted", _DONE_FN),
        ]

    class _HandlerThis(ctypes.Structure):
        _fields_ = [("lpVtbl", ctypes.POINTER(_HandlerVtbl))]

    class _CompletionHandler:
        """Hand written IActivateAudioInterfaceCompletionHandler."""

        def __init__(self, event_handle):
            self.event = event_handle
            self.result: Dict[str, object] = {}
            self._refs = 1
            self._qi = _QI_FN(self._on_qi)
            self._addref = _REF_FN(self._on_addref)
            self._release = _REF_FN(self._on_release)
            self._done = _DONE_FN(self._on_activate_completed)
            self._vtbl = _HandlerVtbl(
                self._qi, self._addref, self._release, self._done)
            self._this = _HandlerThis(ctypes.pointer(self._vtbl))
            self._addr = ctypes.addressof(self._this)
            with _HANDLERS_LOCK:
                _HANDLERS[self._addr] = self
                _ALL_HANDLERS.append(self)

        # -- COM plumbing -------------------------------------------------
        def _on_qi(self, _this, riid, ppv):
            if not ppv:
                return E_NOINTERFACE
            try:
                g = ctypes.cast(_as_ptr(riid), ctypes.POINTER(GUID)).contents
                if (g == IID_IUnknown
                        or g == IID_IActivateAudioInterfaceCompletionHandler
                        or g == IID_IActivateAudioInterfaceCompletionHandler_ALT):
                    ppv[0] = self._addr
                    return S_OK
            except Exception:
                pass
            ppv[0] = None
            return E_NOINTERFACE

        def _on_addref(self, _this):
            self._refs += 1
            return self._refs

        def _on_release(self, _this):
            self._refs -= 1
            return self._refs

        def _on_activate_completed(self, _this, op):
            if op:
                hr = ctypes.c_long(0)
                punk = ctypes.c_void_p()
                try:
                    _vtbl_call(
                        op, 3, ctypes.c_long,
                        [ctypes.POINTER(ctypes.c_long),
                         ctypes.POINTER(ctypes.c_void_p)],
                        ctypes.byref(hr), ctypes.byref(punk))
                    self.result["hr"] = hr.value
                    self.result["client"] = punk.value
                except Exception as exc:  # pragma: no cover
                    self.result["error"] = repr(exc)
            else:
                self.result["error"] = "ActivateCompleted with NULL operation"
            _kernel32.SetEvent(self.event)
            return S_OK

        def handle(self):
            return ctypes.cast(ctypes.pointer(self._this), ctypes.c_void_p)

        def dispose(self):
            with _HANDLERS_LOCK:
                _HANDLERS.pop(self._addr, None)

    _kernel32.SetEvent.argtypes = [HANDLE]
    _kernel32.SetEvent.restype = wintypes.BOOL


# ==========================================================================
#  Public: list_audio_apps
# ==========================================================================
def list_audio_apps() -> List[Dict[str, object]]:
    """Audio sessions of the default render endpoint, playing ones first."""
    if not IS_WINDOWS:
        raise RuntimeError(
            "list_audio_apps() requires Windows (WASAPI is a Windows API).")
    return _list_audio_apps_win()


# ==========================================================================
#  Public: ProcessLoopbackCapture
# ==========================================================================
class ProcessLoopbackCapture:
    """Capture the audio of a single process (or its whole tree)."""

    def __init__(self, pid, samplerate=48000, channels=2, blocksize=1024,
                 include_tree=True):
        self.pid = int(pid)
        self.samplerate = int(samplerate)
        self.channels = int(channels)
        self.blocksize = int(blocksize)
        self.include_tree = bool(include_tree)

        self._error = ""
        self._started = False
        self._client = None
        self._capture = None
        self._event = None
        self._fmt_buf = None
        self._nch = int(channels)
        self._bytes_per_sample = 4
        self._fmt_kind = "float32"
        self._extra_flags = 0
        # diagnostics
        self.frames_captured = 0
        self.discontinuities = 0
        self.silent_packets = 0
        self._com_inited = False
        self._com_thread = None

    # ------------------------------------------------------------------ api
    @property
    def error(self) -> str:
        return self._error

    def start(self) -> bool:
        if not IS_WINDOWS:
            raise RuntimeError(
                "ProcessLoopbackCapture requires Windows "
                "(WASAPI process loopback).")
        if self._started:
            return True
        self._error = ""
        return self._start()

    def read(self, timeout: float = 0.5) -> Optional[np.ndarray]:
        if not IS_WINDOWS:
            return None
        if not self._started or self._capture is None:
            return None
        try:
            return self._read_impl(float(timeout))
        except Exception as exc:  # never let the capture thread die
            self._error = "read failed: %r" % (exc,)
            return None

    def stop(self) -> None:
        if not IS_WINDOWS:
            return
        try:
            self._stop_impl()
        finally:
            self._started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
        return False

    def __del__(self):
        try:
            if getattr(self, "_started", False):
                self.stop()
        except Exception:
            pass

    # ------------------------------------------------------- implementation
    def _fail(self, msg: str) -> bool:
        self._error = msg
        self._cleanup()
        return False

    def _cleanup(self):
        """Release every resource; safe to call more than once."""
        if self._capture:
            _release(self._capture)
            self._capture = None
        if self._client:
            try:
                _vtbl_call(self._client, 11, ctypes.c_long, [])  # Stop
            except Exception:
                pass
            _release(self._client)
            self._client = None
        if self._event:
            try:
                _kernel32.CloseHandle(self._event)
            except Exception:
                pass
            self._event = None
        self._fmt_buf = None
        if self._com_inited:
            if threading.get_ident() == self._com_thread:
                try:
                    _ole32.CoUninitialize()
                except Exception:
                    pass
            self._com_inited = False

    def _start(self) -> bool:
        # ---- COM init for THIS thread (MTA is required by Activate..Async)
        hr = _ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
        if hr == RPC_E_CHANGED_MODE:
            # Thread already in another apartment; continue but don't uninit.
            self._com_inited = False
        elif _hr_ok(hr):
            self._com_inited = True
        else:
            return self._fail("CoInitializeEx failed hr=0x%08X" % (hr & 0xFFFFFFFF))
        self._com_thread = threading.get_ident()

        event = _kernel32.CreateEventW(None, 0, 0, None)
        if not event:
            return self._fail("CreateEventW failed")
        self._event = event

        # ---- activation parameters (VT_BLOB) -------------------------
        params = AUDIOCLIENT_ACTIVATION_PARAMS()
        params.ActivationType = AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK
        params.ProcessLoopbackParams.TargetProcessId = self.pid
        params.ProcessLoopbackParams.ProcessLoopbackMode = (
            AUDCLIENT_PROCESS_LOOPBACK_MODE_INCLUDE_TREE if self.include_tree
            else AUDCLIENT_PROCESS_LOOPBACK_MODE_EXCLUDE_TREE)

        pv = PROPVARIANT()
        pv.vt = VT_BLOB
        pv.u.blob.cbSize = ctypes.sizeof(params)
        pv.u.blob.pBlobData = ctypes.cast(
            ctypes.pointer(params), ctypes.POINTER(ctypes.c_ubyte))

        handler = _CompletionHandler(event)
        async_op = ctypes.c_void_p()
        try:
            hr = _mmdev.ActivateAudioInterfaceAsync(
                DEVICE_NAME_PROCESS_LOOPBACK,
                ctypes.byref(IID_IAudioClient),
                ctypes.byref(pv),
                handler.handle(),
                ctypes.byref(async_op))
        except Exception as exc:
            handler.dispose()
            return self._fail("ActivateAudioInterfaceAsync raised %r" % (exc,))

        if not _hr_ok(hr):
            # keep params alive until here on purpose
            _release(async_op.value)
            handler.dispose()
            return self._fail(
                "ActivateAudioInterfaceAsync failed hr=0x%08X" % (hr & 0xFFFFFFFF))

        wait = _kernel32.WaitForSingleObject(event, 5000)
        if wait == WAIT_TIMEOUT:
            _release(async_op.value)
            handler.dispose()
            return self._fail("ActivateCompleted timed out after 5 s")
        if wait != WAIT_OBJECT_0:
            _release(async_op.value)
            handler.dispose()
            return self._fail("WaitForSingleObject returned 0x%X" % wait)

        if "error" in handler.result:
            err = str(handler.result["error"])
            _release(async_op.value)
            handler.dispose()
            return self._fail("activation error: " + err)

        act_hr = int(handler.result.get("hr", -1))
        client = handler.result.get("client")
        _release(async_op.value)
        handler.dispose()
        if not _hr_ok(act_hr) or not client:
            return self._fail(
                "GetActivateResult hr=0x%08X" % (act_hr & 0xFFFFFFFF))

        self._client = client
        # keep 'params' referenced until after the wait (already done above)
        del params

        # ---- mix format -------------------------------------------------
        # NOTE: on current Windows the *process-loopback* client returns
        # E_NOTIMPL from GetMixFormat (the MS reference sample works around
        # this by hardcoding a PCM format).  So: try the loopback client,
        # then the default render endpoint, then a plain fallback.
        self._extra_flags = 0
        raw = None
        pfmt = ctypes.c_void_p()
        hr = _vtbl_call(self._client, 8, ctypes.c_long,
                        [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(pfmt))
        if _hr_ok(hr) and pfmt.value:
            _w = ctypes.cast(pfmt.value, ctypes.POINTER(WAVEFORMATEX)).contents
            raw = ctypes.string_at(
                pfmt.value, ctypes.sizeof(WAVEFORMATEX) + _w.cbSize)
            _ole32.CoTaskMemFree(pfmt)
        if raw is None:
            raw = self._device_mix_format_bytes()
        if raw is None:
            # last resort: plain 48 kHz stereo float32 + auto conversion
            plain = WAVEFORMATEX()
            plain.wFormatTag = WAVE_FORMAT_IEEE_FLOAT
            plain.nChannels = 2
            plain.nSamplesPerSec = 48000
            plain.wBitsPerSample = 32
            plain.nBlockAlign = 2 * 4
            plain.nAvgBytesPerSec = 48000 * 2 * 4
            plain.cbSize = 0
            raw = bytes(plain)
            self._extra_flags = AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM

        wfx = WAVEFORMATEX()
        ctypes.memmove(ctypes.byref(wfx), raw, ctypes.sizeof(WAVEFORMATEX))
        if wfx.nSamplesPerSec == 0 or wfx.nChannels == 0:
            return self._fail("could not obtain a valid mix format")

        tag = wfx.wFormatTag
        if tag == WAVE_FORMAT_EXTENSIBLE and len(raw) >= 40:
            sub = GUID()
            ctypes.memmove(ctypes.byref(sub), raw[24:40], 16)
            if sub == KSDATAFORMAT_SUBTYPE_IEEE_FLOAT:
                tag = WAVE_FORMAT_IEEE_FLOAT
            elif sub == KSDATAFORMAT_SUBTYPE_PCM:
                tag = WAVE_FORMAT_PCM

        self._nch = int(wfx.nChannels)
        self.samplerate = int(wfx.nSamplesPerSec)
        bits = int(wfx.wBitsPerSample)
        if tag == WAVE_FORMAT_IEEE_FLOAT and bits == 32:
            self._fmt_kind = "float32"
            self._bytes_per_sample = 4
        elif tag == WAVE_FORMAT_PCM and bits == 16:
            self._fmt_kind = "int16"
            self._bytes_per_sample = 2
        elif tag == WAVE_FORMAT_PCM and bits == 32:
            self._fmt_kind = "int32"
            self._bytes_per_sample = 4
        elif tag == WAVE_FORMAT_PCM and bits == 24:
            self._fmt_kind = "int24"
            self._bytes_per_sample = 3
        else:
            # Unknown -> keep mix format, assume float32
            self._fmt_kind = "float32"
            self._bytes_per_sample = max(1, bits // 8)

        self._fmt_buf = ctypes.create_string_buffer(raw, len(raw))

        # ---- Initialize (loopback + event callback) ---------------------
        flags = AUDCLNT_STREAMFLAGS_LOOPBACK | AUDCLNT_STREAMFLAGS_EVENTCALLBACK
        hns = 200000  # 20 ms
        hr = self._init_stream(hns)
        if hr == AUDCLNT_E_BUFFER_SIZE_NOT_ALIGNED:
            dp = ctypes.c_longlong(0)
            _vtbl_call(self._client, 9, ctypes.c_long,
                       [ctypes.POINTER(ctypes.c_longlong),
                        ctypes.POINTER(ctypes.c_longlong)],
                       ctypes.byref(dp), None)
            period = dp.value if dp.value > 0 else 200000
            sr = max(1, self.samplerate)
            frames = int(0.5 + period * sr / 10000000.0)
            hns = int(10000000.0 * frames / sr + 0.5)
            hr = self._init_stream(hns)
        if hr == AUDCLNT_E_UNSUPPORTED_FORMAT:
            # retry with a plain (non-extensible) WAVEFORMATEX
            plain = WAVEFORMATEX()
            plain.wFormatTag = tag if tag != WAVE_FORMAT_EXTENSIBLE else WAVE_FORMAT_PCM
            plain.nChannels = wfx.nChannels
            plain.nSamplesPerSec = wfx.nSamplesPerSec
            plain.nAvgBytesPerSec = self.samplerate * self._nch * self._bytes_per_sample
            plain.nBlockAlign = self._nch * self._bytes_per_sample
            plain.wBitsPerSample = bits
            plain.cbSize = 0
            self._fmt_buf = plain
            hr = self._init_stream(hns)
        if not _hr_ok(hr):
            return self._fail("IAudioClient::Initialize failed hr=0x%08X"
                              % (hr & 0xFFFFFFFF))

        # ---- event handle + capture client + start ----------------------
        hr = _vtbl_call(self._client, 13, ctypes.c_long, [ctypes.c_void_p],
                        ctypes.c_void_p(event))
        if not _hr_ok(hr):
            return self._fail("SetEventHandle failed hr=0x%08X" % (hr & 0xFFFFFFFF))

        cap = ctypes.c_void_p()
        hr = _vtbl_call(self._client, 14, ctypes.c_long,
                        [ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)],
                        ctypes.byref(IID_IAudioCaptureClient), ctypes.byref(cap))
        if not _hr_ok(hr) or not cap.value:
            return self._fail("GetService(IAudioCaptureClient) failed hr=0x%08X"
                              % (hr & 0xFFFFFFFF))
        self._capture = cap.value

        hr = _vtbl_call(self._client, 10, ctypes.c_long, [])
        if not _hr_ok(hr):
            return self._fail("IAudioClient::Start failed hr=0x%08X"
                              % (hr & 0xFFFFFFFF))

        self.frames_captured = 0
        self.discontinuities = 0
        self.silent_packets = 0
        self._started = True
        return True

    def _init_stream(self, hns: int) -> int:
        fmt_ptr = ctypes.cast(self._fmt_buf, ctypes.POINTER(WAVEFORMATEX))
        flags = (AUDCLNT_STREAMFLAGS_LOOPBACK | AUDCLNT_STREAMFLAGS_EVENTCALLBACK
                 | getattr(self, "_extra_flags", 0))
        return _vtbl_call(
            self._client, 3, ctypes.c_long,
            [ctypes.c_int, ctypes.c_ulong, ctypes.c_longlong, ctypes.c_longlong,
             ctypes.POINTER(WAVEFORMATEX), ctypes.POINTER(GUID)],
            AUDCLNT_SHAREMODE_SHARED, flags, hns, 0, fmt_ptr, None)

    def _device_mix_format_bytes(self):
        """Mix format (raw WAVEFORMATEX bytes) of the default render endpoint."""
        enum = ctypes.c_void_p()
        device = ctypes.c_void_p()
        client = ctypes.c_void_p()
        pfmt = ctypes.c_void_p()
        try:
            hr = _ole32.CoCreateInstance(
                ctypes.byref(CLSID_MMDeviceEnumerator), None, CLSCTX_ALL,
                ctypes.byref(IID_IMMDeviceEnumerator), ctypes.byref(enum))
            if not _hr_ok(hr):
                return None
            hr = _vtbl_call(enum, 4, ctypes.c_long,
                            [ctypes.c_int, ctypes.c_int,
                             ctypes.POINTER(ctypes.c_void_p)], 0, 0,
                            ctypes.byref(device))
            if not _hr_ok(hr):
                return None
            hr = _vtbl_call(device, 3, ctypes.c_long,
                            [ctypes.POINTER(GUID), ctypes.c_ulong,
                             ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
                            ctypes.byref(IID_IAudioClient), 0, None,
                            ctypes.byref(client))
            if not _hr_ok(hr):
                return None
            hr = _vtbl_call(client, 8, ctypes.c_long,
                            [ctypes.POINTER(ctypes.c_void_p)],
                            ctypes.byref(pfmt))
            if not _hr_ok(hr) or not pfmt.value:
                return None
            w = ctypes.cast(pfmt.value, ctypes.POINTER(WAVEFORMATEX)).contents
            raw = ctypes.string_at(
                pfmt.value, ctypes.sizeof(WAVEFORMATEX) + w.cbSize)
            _ole32.CoTaskMemFree(pfmt)
            pfmt = ctypes.c_void_p()
            return raw
        except Exception:
            return None
        finally:
            _release(client)
            _release(device)
            _release(enum)

    def _stop_impl(self):
        self._cleanup()

    # ------------------------------------------------------------ read loop
    def _read_impl(self, timeout: float) -> Optional[np.ndarray]:
        deadline = time.monotonic() + max(0.0, timeout)
        chunks: List[np.ndarray] = []
        while True:
            got = self._drain(chunks)
            if got:
                break
            if time.monotonic() >= deadline:
                return None
            remaining = deadline - time.monotonic()
            ms = int(max(1, min(50, remaining * 1000)))
            _kernel32.WaitForSingleObject(self._event, ms)
        if not chunks:
            return None
        return np.concatenate(chunks, axis=0)

    def _drain(self, chunks: List[np.ndarray]) -> bool:
        got = False
        while True:
            n = ctypes.c_ulong(0)
            hr = _vtbl_call(self._capture, 5, ctypes.c_long,
                            [ctypes.POINTER(ctypes.c_ulong)], ctypes.byref(n))
            if not _hr_ok(hr):
                self._error = ("GetNextPacketSize hr=0x%08X"
                               % (hr & 0xFFFFFFFF))
                break
            if n.value == 0:
                break

            pdata = ctypes.c_void_p()
            frames = ctypes.c_ulong(0)
            bflags = ctypes.c_ulong(0)
            devpos = ctypes.c_ulonglong(0)
            qpcpos = ctypes.c_ulonglong(0)
            hr = _vtbl_call(
                self._capture, 3, ctypes.c_long,
                [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_ulong),
                 ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulonglong),
                 ctypes.POINTER(ctypes.c_ulonglong)],
                ctypes.byref(pdata), ctypes.byref(frames), ctypes.byref(bflags),
                ctypes.byref(devpos), ctypes.byref(qpcpos))
            if hr == AUDCLNT_S_BUFFER_EMPTY:
                break
            if not _hr_ok(hr):
                self._error = "GetBuffer hr=0x%08X" % (hr & 0xFFFFFFFF)
                break

            nframes = int(frames.value)
            fl = int(bflags.value)
            if fl & AUDCLNT_BUFFERFLAGS_SILENT:
                self.silent_packets += 1
            if fl & AUDCLNT_BUFFERFLAGS_DATA_DISCONTINUITY:
                self.discontinuities += 1
            arr = self._decode(pdata.value, nframes, fl)
            # always release the packet, even if decoding failed
            _vtbl_call(self._capture, 4, ctypes.c_long, [ctypes.c_ulong],
                       ctypes.c_ulong(nframes))
            if arr is not None:
                chunks.append(arr)
                self.frames_captured += nframes
                got = True
        return got

    def _decode(self, ptr, nframes, flags) -> Optional[np.ndarray]:
        nch = self._nch
        if nframes <= 0 or nch <= 0:
            return None
        if (flags & AUDCLNT_BUFFERFLAGS_SILENT) or not ptr:
            return np.zeros((nframes, nch), dtype=np.float32)
        nbytes = nframes * nch * self._bytes_per_sample
        raw = ctypes.string_at(ptr, nbytes)
        kind = self._fmt_kind
        if kind == "float32":
            arr = np.frombuffer(raw, dtype="<f4")
        elif kind == "int16":
            arr = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        elif kind == "int32":
            arr = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
        elif kind == "int24":
            b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
            v = (b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16))
            v = np.where(v & 0x800000, v - 0x1000000, v)
            arr = v.astype(np.float32) / 8388608.0
        else:
            arr = np.frombuffer(raw, dtype="<f4")
        need = nframes * nch
        if arr.size < need:
            arr = np.concatenate([arr, np.zeros(need - arr.size, np.float32)])
        else:
            arr = arr[:need]
        return np.ascontiguousarray(arr.reshape(nframes, nch), dtype=np.float32)


# ==========================================================================
#  Windows-only: session enumeration
# ==========================================================================
def _list_audio_apps_win() -> List[Dict[str, object]]:  # pragma: no cover
    out: List[Dict[str, object]] = []
    hr = _ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    com_inited = _hr_ok(hr)
    enum = ctypes.c_void_p()
    device = ctypes.c_void_p()
    asm = ctypes.c_void_p()
    sessions = ctypes.c_void_p()
    try:
        hr = _ole32.CoCreateInstance(
            ctypes.byref(CLSID_MMDeviceEnumerator), None, CLSCTX_ALL,
            ctypes.byref(IID_IMMDeviceEnumerator), ctypes.byref(enum))
        if not _hr_ok(hr):
            raise CaptureError("CoCreateInstance(MMDeviceEnumerator) hr=0x%08X"
                               % (hr & 0xFFFFFFFF))

        # GetDefaultAudioEndpoint(eRender=0, eConsole=0, &device)
        hr = _vtbl_call(enum, 4, ctypes.c_long,
                        [ctypes.c_int, ctypes.c_int,
                         ctypes.POINTER(ctypes.c_void_p)], 0, 0,
                        ctypes.byref(device))
        if not _hr_ok(hr):
            raise CaptureError("GetDefaultAudioEndpoint hr=0x%08X"
                               % (hr & 0xFFFFFFFF))

        # IMMDevice::Activate(REFIID, DWORD clsctx, PROPVARIANT*, void**)
        hr = _vtbl_call(device, 3, ctypes.c_long,
                        [ctypes.POINTER(GUID), ctypes.c_ulong,
                         ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
                        ctypes.byref(IID_IAudioSessionManager2), 0, None,
                        ctypes.byref(asm))
        if not _hr_ok(hr):
            raise CaptureError("Activate(IAudioSessionManager2) hr=0x%08X"
                               % (hr & 0xFFFFFFFF))

        hr = _vtbl_call(asm, 5, ctypes.c_long,
                        [ctypes.POINTER(ctypes.c_void_p)],
                        ctypes.byref(sessions))
        if not _hr_ok(hr):
            raise CaptureError("GetSessionEnumerator hr=0x%08X"
                               % (hr & 0xFFFFFFFF))

        count = ctypes.c_int(0)
        hr = _vtbl_call(sessions, 3, ctypes.c_long,
                        [ctypes.POINTER(ctypes.c_int)], ctypes.byref(count))
        if not _hr_ok(hr):
            raise CaptureError("GetCount hr=0x%08X" % (hr & 0xFFFFFFFF))

        seen = set()
        for i in range(max(0, count.value)):
            ctrl = ctypes.c_void_p()
            hr = _vtbl_call(sessions, 4, ctypes.c_long,
                            [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)],
                            i, ctypes.byref(ctrl))
            if not _hr_ok(hr) or not ctrl.value:
                continue
            ctrl2 = ctypes.c_void_p()
            hr = _vtbl_call(ctrl, 0, ctypes.c_long,
                            [ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)],
                            ctypes.byref(IID_IAudioSessionControl2),
                            ctypes.byref(ctrl2))
            if not _hr_ok(hr) or not ctrl2.value:
                _release(ctrl)
                continue
            try:
                info = _session_info(ctrl2)
            except Exception:
                info = None
            _release(ctrl2)
            _release(ctrl)
            if not info:
                continue
            key = info["pid"]
            if key in seen:
                continue
            seen.add(key)
            out.append(info)
    finally:
        _release(sessions)
        _release(asm)
        _release(device)
        _release(enum)
        if com_inited:
            _ole32.CoUninitialize()

    out.sort(key=lambda d: (not d["playing"], str(d["name"]).lower()))
    return out


def _session_info(ctrl2) -> Optional[Dict[str, object]]:  # pragma: no cover
    state = ctypes.c_int(0)
    hr = _vtbl_call(ctrl2, 3, ctypes.c_long, [ctypes.POINTER(ctypes.c_int)],
                    ctypes.byref(state))
    if not _hr_ok(hr):
        return None

    # IAudioSessionControl2::GetProcessId  -> vtable index 14
    pid = ctypes.c_ulong(0)
    hr = _vtbl_call(ctrl2, 14, ctypes.c_long, [ctypes.POINTER(ctypes.c_ulong)],
                    ctypes.byref(pid))
    getpid_ok = _hr_ok(hr)

    # IAudioSessionControl::GetDisplayName -> vtable index 4
    name = ""
    pstr = wintypes.LPWSTR()
    try:
        hr = _vtbl_call(ctrl2, 4, ctypes.c_long,
                        [ctypes.POINTER(wintypes.LPWSTR)], ctypes.byref(pstr))
        if _hr_ok(hr) and pstr.value:
            name = str(pstr.value)
    finally:
        if pstr:
            _ole32.CoTaskMemFree(pstr)

    if not getpid_ok or not pid.value:
        if not name:
            return None
        # System-sounds session has no pid; keep it with pid 0
        return {"pid": 0, "name": name, "exe": "", "playing": state.value == 1}

    the_pid = int(pid.value)
    exe = _proc_exe(the_pid)
    if not name:
        name = _session_prop_name(ctrl2)
    if not name and exe:
        name = exe.rsplit("\\", 1)[-1]
    if not name:
        name = "PID %d" % the_pid
    return {"pid": the_pid, "name": name, "exe": exe,
            "playing": state.value == 1}


def _proc_exe(pid: int) -> str:  # pragma: no cover
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        size = ctypes.c_ulong(1024)
        buf = ctypes.create_unicode_buffer(1024)
        if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        _kernel32.CloseHandle(h)


def _session_prop_name(ctrl2) -> str:  # pragma: no cover
    """Try PKEY_SYSTEM_NAME through IPropertyStore (best effort)."""
    store = ctypes.c_void_p()
    hr = _vtbl_call(ctrl2, 0, ctypes.c_long,
                    [ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)],
                    ctypes.byref(IID_IPropertyStore), ctypes.byref(store))
    if not _hr_ok(hr) or not store.value:
        return ""
    try:
        key = PROPERTYKEY()
        ctypes.memmove(ctypes.byref(key), ctypes.byref(FMTID_SYSTEM_NAME),
                       ctypes.sizeof(GUID))
        key.pid = PID_SYSTEM_NAME
        pv = PROPVARIANT()
        # IPropertyStore::GetValue -> vtable index 5
        hr = _vtbl_call(store, 5, ctypes.c_long,
                        [ctypes.POINTER(PROPERTYKEY), ctypes.POINTER(PROPVARIANT)],
                        ctypes.byref(key), ctypes.byref(pv))
        if not _hr_ok(hr):
            return ""
        val = ""
        if pv.vt == VT_LPWSTR and pv.u.pwszVal:
            val = str(pv.u.pwszVal)
        _ole32.PropVariantClear(ctypes.byref(pv))
        return val
    finally:
        _release(store)
