# ==========================================
# 1. 构建阶段 (Builder)
# ==========================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 安装编译依赖，构建 Python Wheel 依赖包
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libffi-dev libssl-dev git curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 将依赖编译并预装到本地 wheel 缓存/目标目录中
RUN python -m pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ==========================================
# 2. 运行阶段 (Runner)
# ==========================================
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API__HOST=0.0.0.0 \
    API__PORT=8000

WORKDIR /app

# 安装运行时必需的动态库（如 curl，排除编译工具）
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段仅复制预编译好的依赖包并安装
COPY --from=builder /app/wheels /wheels
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# 安全优化：创建非 root 专有用户并切换
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 仅复制代码文件（结合 .dockerignore 排除多余文件）
COPY --chown=appuser:appuser . .

EXPOSE 8000

# 增加容器健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["python", "-m", "scripts.entrypoint"]
CMD ["start"]