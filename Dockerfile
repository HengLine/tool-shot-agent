# ==========================================
# 1. 构建阶段 (Builder)
# ==========================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 安装底层 C/C++ 依赖（满足 Pillow, numpy, cffi 等包的编译依赖）
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libffi-dev libssl-dev git curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖配置文件与项目自述文件（setuptools 构建所需的元数据）
COPY pyproject.toml README.md ./
COPY src/ ./src/

# 从 pyproject.toml 构建项目的 Wheel 依赖包以及项目自身
RUN python -m pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels . \
    && pip wheel --no-cache-dir --wheel-dir /app/wheels -r <(python -c "import tomli; print('\n'.join(tomli.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" 2>/dev/null || pip install build && python -m build -w -o /app/wheels)


# ==========================================
# 2. 运行阶段 (Runner)
# ==========================================
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PENSHOT_API__HOST=0.0.0.0 \
    PENSHOT_API__PORT=8000

WORKDIR /app

# 安装运行基础工具
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制预编译好的依赖库并安装
COPY --from=builder /app/wheels /wheels
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# 安全配置：创建 appuser 非 root 专属用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 拷贝完整应用代码
COPY --chown=appuser:appuser . .

EXPOSE 8000

# 容器健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动入口（根据 story-shot-agent 的脚本入口配置）
ENTRYPOINT ["python", "-m", "scripts.entrypoint"]
CMD ["start"]