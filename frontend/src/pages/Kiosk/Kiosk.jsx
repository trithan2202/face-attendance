import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Camera, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../../services/api';

const captureJpeg = (video) => new Promise((resolve, reject) => {
  if (!video?.videoWidth) return reject(new Error('Camera chưa sẵn sàng'));
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Không thể chụp frame')), 'image/jpeg', 0.82);
});

const Kiosk = () => {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const sessionRef = useRef(null);
  const busyRef = useRef(false);
  const mountedRef = useRef(false);
  const retryTimerRef = useRef(null);
  const [status, setStatus] = useState('starting');
  const [message, setMessage] = useState('Đang mở camera...');
  const [result, setResult] = useState(null);
  const [holdProgress, setHoldProgress] = useState({ current: 0, required: 3 });

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  const scheduleReset = useCallback(() => {
    clearTimeout(retryTimerRef.current);
    retryTimerRef.current = setTimeout(() => {
      if (mountedRef.current) resetCycle();
    }, 5000);
  // resetCycle is stable and is resolved when this callback runs.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetCycle = useCallback(async () => {
    try {
      setResult(null);
      setHoldProgress({ current: 0, required: 3 });
      const health = await api.system.workerStatus().catch(() => null);
      if (health && !health.online) setMessage('Worker camera đang offline; kiosk vẫn dùng camera trình duyệt');
      const recognition = await api.kiosk.startRecognition();
      sessionRef.current = { id: recognition.session_id };
      setStatus('recognizing');
      setMessage(recognition.message);
    } catch (err) {
      sessionRef.current = null;
      if (err?.status === 0) stopCamera();
      setStatus('error');
      setMessage(err.message || 'Không thể kết nối đến backend');
      setResult({ error: err.message || 'Không thể kết nối đến backend', backendOffline: err?.status === 0 });
    }
  }, [stopCamera]);

  useEffect(() => {
    let active = true;
    mountedRef.current = true;
    navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false })
      .then(stream => {
        if (!active) { stream.getTracks().forEach(track => track.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        return resetCycle();
      })
      .catch(err => {
        setStatus('camera-error');
        setMessage(err.message || 'Không thể truy cập camera');
      });
    return () => {
      active = false;
      mountedRef.current = false;
      clearTimeout(retryTimerRef.current);
      stopCamera();
    };
  }, [resetCycle, stopCamera]);

  useEffect(() => {
    if (status !== 'recognizing') return undefined;
    let active = true;
    const submit = async () => {
      if (!active || busyRef.current || !sessionRef.current) return;
      busyRef.current = true;
      try {
        const blob = await captureJpeg(videoRef.current);
        const response = await api.kiosk.submitRecognitionFrame(sessionRef.current.id, blob);
        setMessage(response.message);
        setHoldProgress({ current: response.stable_seconds, required: response.required_seconds });
        if (response.state === 'COMPLETED') {
          sessionRef.current = null;
          setStatus('success');
          setResult(response);
          scheduleReset();
        } else if (response.state === 'COOLDOWN') {
          sessionRef.current = null;
          setStatus('error');
          setResult({ error: response.message });
          scheduleReset();
        } else if (response.state === 'FAILED') {
          throw new Error(response.message);
        }
      } catch (err) {
        sessionRef.current = null;
        const backendOffline = err?.status === 0;
        if (backendOffline) stopCamera();
        setStatus('error');
        setMessage(err.message || 'Nhận diện thất bại');
        setResult({ error: err.message || 'Nhận diện thất bại', backendOffline });
        if (!backendOffline) scheduleReset();
      } finally { busyRef.current = false; }
    };
    const timer = setInterval(submit, 350);
    return () => { active = false; clearInterval(timer); };
  }, [status, resetCycle, scheduleReset, stopCamera]);

  if (status === 'camera-error' || result?.backendOffline) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-neutral-900 p-6 text-center">
      {result?.backendOffline
        ? <XCircle className="w-24 h-24 text-danger-500 mb-6" />
        : <Camera className="w-24 h-24 text-neutral-600 mb-6" />}
      <h2 className="text-2xl font-bold mb-2">
        {result?.backendOffline ? 'Backend đang ngoại tuyến' : 'Không thể mở camera'}
      </h2>
      <p className="text-neutral-400 max-w-md mb-8">{message}</p>
      <button onClick={() => window.location.reload()} className="px-6 py-3 bg-primary-600 rounded-md font-medium">Thử kết nối lại</button>
    </div>
  );

  return (
    <div className="relative w-full h-screen flex items-center justify-center bg-neutral-900 overflow-hidden">
      <div className="absolute top-8 left-8 z-20 px-4 py-2 rounded-full font-medium bg-neutral-800/80 border border-neutral-700">
        {message}
      </div>
      <div className="relative w-full max-w-5xl aspect-video rounded-2xl overflow-hidden border border-neutral-700 shadow-2xl bg-neutral-800">
        <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover -scale-x-100" />
        {status === 'recognizing' && (
          <>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 border-2 border-primary-500 rounded-3xl shadow-[0_0_40px_rgba(99,102,241,0.5)]" />
            <div className="absolute inset-x-8 bottom-8 h-3 bg-black/60 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 transition-all duration-300"
                style={{ width: `${Math.min(100, (holdProgress.current / holdProgress.required) * 100)}%` }}
              />
            </div>
          </>
        )}
      </div>
      {(status === 'success' || status === 'error') && (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-30 w-full max-w-2xl px-4">
          <div className={`p-6 rounded-2xl shadow-2xl flex items-center gap-6 text-white ${status === 'success' ? 'bg-success-600' : 'bg-danger-600'}`}>
            {status === 'success' ? <CheckCircle className="w-16 h-16" /> : <XCircle className="w-16 h-16" />}
            <div><h2 className="text-3xl font-bold mb-2">{status === 'success' ? (result.event_type === 'CHECK_OUT' ? 'Check-out successful' : 'Check-in successful') : 'Unable to record attendance'}</h2>
              <p className="text-lg">{status === 'success' ? `${result.full_name} (${result.employee_code})` : result?.error}</p></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Kiosk;
