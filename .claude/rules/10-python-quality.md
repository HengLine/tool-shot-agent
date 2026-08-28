# Python 质量规则

## 版本与工具

- Python 版本以 `pyproject.toml` 的 `requires-python` 为准；当前项目要求 Python 3.10 或更高版本。
- Python lint 使用 Ruff，格式化使用 Ruff format。
- 类型检查使用 mypy。
- Markdown 检查和格式化使用 mdformat。
- Pre-commit 的实际 hook 以 `.pre-commit-config.yaml` 为准。
- Black、isort 和 flake8 不作为当前 pre-commit 流程的规范依据。

## 代码约定

- 优先复用现有模块、类型、异常、日志和依赖注入方式。
- 保持异步路径非阻塞；不得在事件循环中直接执行已知的阻塞操作。
- 公共函数和新增模块遵循现有中文注释与文档字符串约定，并补充必要的类型标注。
- 异常应保留原始上下文；不要用宽泛捕获掩盖可定位的错误。
- 不为不存在的边界场景增加无依据的 fallback、兼容层或抽象。

## 测试约定

- 测试框架和 asyncio 行为以 `pyproject.toml` 为准；先运行受影响范围的测试。
- 不因项目配置已启用自动异步模式而强制新增无必要的 asyncio 标记。
- 外部 LLM、Redis、Chroma 或其他服务需要相应环境；未配置时明确标记为未验证。
- 不擅自增加覆盖率阈值，不把未执行的测试写成通过。

## 建议验证顺序

```bash
pytest <受影响的测试路径>
ruff check <受影响的路径>
ruff format --check <受影响的路径>
mypy src/
pre-commit run --all-files
```

根据改动范围选择命令，不要求每次默认执行全部慢速或外部依赖测试。