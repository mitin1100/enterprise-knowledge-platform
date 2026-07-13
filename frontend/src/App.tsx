import { useEffect, useState } from "react";


type HealthResponse = {
  status: string;
  service: string;
};


const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  "http://localhost:8000/api/v1";


export default function App() {
  const [health, setHealth] =
    useState<HealthResponse | null>(null);

  const [error, setError] =
    useState<string | null>(null);


  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/health`,
        );

        if (!response.ok) {
          throw new Error(
            `Backend trả về HTTP ${response.status}`,
          );
        }

        const data =
          (await response.json()) as HealthResponse;

        setHealth(data);
      } catch (requestError) {
        if (requestError instanceof Error) {
          setError(requestError.message);
        } else {
          setError("Đã xảy ra lỗi không xác định");
        }
      }
    };

    checkBackendHealth();
  }, []);


  let statusClass = "loading";
  let statusMessage = "Đang kiểm tra backend...";

  if (health) {
    statusClass = "success";
    statusMessage =
      `Backend: ${health.status} — ${health.service}`;
  }

  if (error) {
    statusClass = "error";
    statusMessage =
      `Không kết nối được backend: ${error}`;
  }


  return (
    <main className="page">
      <section className="card">
        <span className="eyebrow">
          Phase 1 · Project Setup
        </span>

        <h1>
          AI Enterprise Knowledge Platform
        </h1>

        <p>
          React frontend đang kiểm tra kết nối
          tới FastAPI backend.
        </p>

        <div className={`status ${statusClass}`}>
          {statusMessage}
        </div>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
        >
          Mở Swagger API
        </a>
      </section>
    </main>
  );
}