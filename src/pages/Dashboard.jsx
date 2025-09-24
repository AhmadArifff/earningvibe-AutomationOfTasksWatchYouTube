import { useEffect, useRef, useState } from "react";

export default function Dashboard() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({ tasks_done: 0, reward_today: 0, balance: "0 USDT" });
  const [running, setRunning] = useState(false);
  const evtSourceRef = useRef(null);

  // helper: fetch stats once
  const fetchStats = async () => {
    try {
      const res = await fetch("/api/stats");
      if (!res.ok) return;
      const data = await res.json();
      setStats((prev) => ({ ...prev, ...data }));
    } catch (e) {
      console.error("fetchStats error", e);
    }
  };

  // Setup EventSource for logs (SSE)
  useEffect(() => {
    // close previous if any
    if (evtSourceRef.current) {
      try { evtSourceRef.current.close(); } catch {}
      evtSourceRef.current = null;
    }

    // const es = new EventSource("/api/logs"); // use proxy or full url
    const es = new EventSource("http://127.0.0.1:5000/api/logs");
    evtSourceRef.current = es;

    es.onopen = () => {
        console.log("✅ SSE connected ke backend");
    };

    es.onerror = (err) => {
        console.error("❌ SSE error:", err);
    };


    es.onmessage = async (e) => {
      // push new log (kept max 400 lines)
      setLogs((prev) => {
        const next = [...prev, e.data].filter(Boolean);
        if (next.length > 400) return next.slice(next.length - 400);
        return next;
      });
      // update stats immediately after each log (server updates stats)
      await fetchStats();

      // heuristic: detect "started" / "stopping" messages to set running flag
      const text = (e.data || "").toLowerCase();
      if (text.includes("mulai") || text.includes("start") || text.includes("start tasks") || text.includes("worker")) {
        setRunning(true);
      }
      if (text.includes("stop") || text.includes("dihentikan") || text.includes("stopping") || text.includes("worker tasks selesai")) {
        setRunning(false);
      }
    };

    // initial stats snapshot
    fetchStats();

    return () => {
      try { es.close(); } catch {}
    };
  }, []);

  const startTasks = async () => {
    try {
      setRunning(true);
      setLogs((p) => [...p, "🚀 Start tasks dikirim ke backend"]);
      const res = await fetch("/api/start-tasks", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        // server will stream logs; we optimistically set running true
      } else {
        setLogs((p) => [...p, `❌ Gagal start: ${data.message || res.status}`]);
        setRunning(false);
      }
      // update stats
      await fetchStats();
    } catch (err) {
      console.error(err);
      setLogs((p) => [...p, "⚠️ Gagal start tasks (koneksi)"]);
      setRunning(false);
    }
  };

  const stopTasks = async () => {
    try {
      setLogs((p) => [...p, "🛑 Stop signal dikirim ke backend"]);
      const res = await fetch("/api/stop-tasks", { method: "POST" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setLogs((p) => [...p, `❌ Gagal stop: ${data.message || res.status}`]);
      }
      // backend will emit log "Stop signal diterima..."
      // we don't forcibly set running=false here; wait for SSE confirmation
    } catch (err) {
      console.error(err);
      setLogs((p) => [...p, "⚠️ Gagal stop tasks (koneksi)"]);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">⚡ Dashboard</h2>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white shadow p-4 rounded-xl">
          <p className="text-gray-500">Tasks Done</p>
          <p className="text-3xl font-bold">{stats.tasks_done}</p>
        </div>
        <div className="bg-white shadow p-4 rounded-xl">
          <p className="text-gray-500">Reward Today</p>
          <p className="text-3xl font-bold">{stats.reward_today}</p>
        </div>
        <div className="bg-white shadow p-4 rounded-xl">
          <p className="text-gray-500">Balance</p>
          <p className="text-3xl font-bold">{stats.balance}</p>
        </div>
      </div>

      <div className="flex gap-4 mb-4">
        <button
          onClick={startTasks}
          disabled={running}
          className={`px-6 py-3 rounded-xl shadow text-white ${running ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"}`}
        >
          🚀 Start Tasks
        </button>
        <button
          onClick={stopTasks}
          disabled={!running}
          className={`px-6 py-3 rounded-xl shadow text-white ${!running ? "bg-gray-400 cursor-not-allowed" : "bg-red-600 hover:bg-red-700"}`}
        >
          🛑 Stop Tasks
        </button>
        <div className="ml-auto self-center text-sm text-gray-600">
          {running ? <span className="text-green-600 font-medium">Running</span> : <span className="text-red-600 font-medium">Stopped</span>}
        </div>
      </div>

      <div className="bg-black text-green-400 mt-6 p-4 rounded-lg h-96 overflow-y-scroll font-mono text-sm">
        {logs.length === 0 && <div className="text-gray-500">No logs yet</div>}
        {logs.map((log, i) => (
          <div key={i} className="mb-1 whitespace-pre-wrap">{log}</div>
        ))}
      </div>
    </div>
  );
}
