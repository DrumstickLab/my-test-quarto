# my-book

这是 Quarto 写书练习的独立测试项目。工作流校验结构并分别构建 HTML 和中文 PDF。正文中的图片、表格、公式与引文用于验证生成结果。

## 已验证的练习节点

| 章 | 提交 |
| --- | --- |
| 1 | `289b82c` |
| 2 | `f5b6f08` |
| 3 | `5cbd3fd` |
| 4 | `283cffe` |
| 5 | `98b3dc3` |
| 6 | 主分支上的校验与发布流程 |

在仓库根目录用 `.quarto-version` 指定的 Quarto 运行以下命令。

```bash
python3 scripts/validate.py
quarto render
```

三份产物位于 `_book/index.html`、`_book/my-book.pdf` 和 `_book/my-book.epub`。PDF 使用 XeLaTeX、ctexbook 和 Fandol，工作流列出了 Linux 上的依赖。
