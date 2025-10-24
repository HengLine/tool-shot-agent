# 剧本分镜智能体 (Script-to-Shot AI Agent)

一个基于多智能体协作的AI系统，能够将剧本智能拆分为短视频脚本单元，生成高质量分镜描述，并保证叙事连续性。支持多种AI提供商，具有强大的可扩展性和易用性。

> 将**一段自然语言中文剧本** → 自动拆分为 **N 个 5 秒分镜**，每个分镜包含：
>
> - 中文画面描述（供人读）
> - 英文 AI 视频提示词（供 Runway/Pika/Sora 使用）
> - 角色连续性锚点（防漂移）
> - 镜头语言建议



## 核心功能

![SVG content](data:image/svg+xml;utf8,%3Csvg%20id%3D%22mermaid-908164f6-4902-4670-861f-d89f7c52a5df%22%20width%3D%22100%25%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20style%3D%22max-width%3A%201431.697509765625px%3B%22%20viewBox%3D%22-8.000007629394531%20-8%201431.697509765625%20240.6344451904297%22%20role%3D%22graphics-document%20document%22%20aria-roledescription%3D%22flowchart-v2%22%3E%3Cstyle%3E%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%7Bfont-family%3A%22trebuchet%20ms%22%2Cverdana%2Carial%2Csans-serif%3Bfont-size%3A16px%3Bfill%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.error-icon%7Bfill%3A%23552222%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.error-text%7Bfill%3A%23552222%3Bstroke%3A%23552222%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edge-thickness-normal%7Bstroke-width%3A2px%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edge-thickness-thick%7Bstroke-width%3A3.5px%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edge-pattern-solid%7Bstroke-dasharray%3A0%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edge-pattern-dashed%7Bstroke-dasharray%3A3%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edge-pattern-dotted%7Bstroke-dasharray%3A2%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.marker%7Bfill%3A%23333333%3Bstroke%3A%23333333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.marker.cross%7Bstroke%3A%23333333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20svg%7Bfont-family%3A%22trebuchet%20ms%22%2Cverdana%2Carial%2Csans-serif%3Bfont-size%3A16px%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.label%7Bfont-family%3A%22trebuchet%20ms%22%2Cverdana%2Carial%2Csans-serif%3Bcolor%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.cluster-label%20text%7Bfill%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.cluster-label%20span%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20p%7Bcolor%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.label%20text%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20span%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20p%7Bfill%3A%23333%3Bcolor%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node%20rect%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node%20circle%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node%20ellipse%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node%20polygon%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node%20path%7Bfill%3A%23ECECFF%3Bstroke%3A%239370DB%3Bstroke-width%3A1px%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.flowchart-label%20text%7Btext-anchor%3Amiddle%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node%20.katex%20path%7Bfill%3A%23000%3Bstroke%3A%23000%3Bstroke-width%3A1px%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node%20.label%7Btext-align%3Acenter%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.node.clickable%7Bcursor%3Apointer%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.arrowheadPath%7Bfill%3A%23333333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edgePath%20.path%7Bstroke%3A%23333333%3Bstroke-width%3A2.0px%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.flowchart-link%7Bstroke%3A%23333333%3Bfill%3Anone%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edgeLabel%7Bbackground-color%3A%23e8e8e8%3Btext-align%3Acenter%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.edgeLabel%20rect%7Bopacity%3A0.5%3Bbackground-color%3A%23e8e8e8%3Bfill%3A%23e8e8e8%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.labelBkg%7Bbackground-color%3Argba(232%2C%20232%2C%20232%2C%200.5)%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.cluster%20rect%7Bfill%3A%23ffffde%3Bstroke%3A%23aaaa33%3Bstroke-width%3A1px%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.cluster%20text%7Bfill%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.cluster%20span%2C%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20p%7Bcolor%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20div.mermaidTooltip%7Bposition%3Aabsolute%3Btext-align%3Acenter%3Bmax-width%3A200px%3Bpadding%3A2px%3Bfont-family%3A%22trebuchet%20ms%22%2Cverdana%2Carial%2Csans-serif%3Bfont-size%3A12px%3Bbackground%3Ahsl(80%2C%20100%25%2C%2096.2745098039%25)%3Bborder%3A1px%20solid%20%23aaaa33%3Bborder-radius%3A2px%3Bpointer-events%3Anone%3Bz-index%3A100%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20.flowchartTitleText%7Btext-anchor%3Amiddle%3Bfont-size%3A18px%3Bfill%3A%23333%3B%7D%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df%20%3Aroot%7B--mermaid-font-family%3A%22trebuchet%20ms%22%2Cverdana%2Carial%2Csans-serif%3B%7D%3C%2Fstyle%3E%3Cg%3E%3Cmarker%20id%3D%22mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd%22%20class%3D%22marker%20flowchart%22%20viewBox%3D%220%200%2010%2010%22%20refX%3D%226%22%20refY%3D%225%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2212%22%20markerHeight%3D%2212%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%200%200%20L%2010%205%20L%200%2010%20z%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointStart%22%20class%3D%22marker%20flowchart%22%20viewBox%3D%220%200%2010%2010%22%20refX%3D%224.5%22%20refY%3D%225%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2212%22%20markerHeight%3D%2212%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%200%205%20L%2010%2010%20L%2010%200%20z%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-circleEnd%22%20class%3D%22marker%20flowchart%22%20viewBox%3D%220%200%2010%2010%22%20refX%3D%2211%22%20refY%3D%225%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Ccircle%20cx%3D%225%22%20cy%3D%225%22%20r%3D%225%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fcircle%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-circleStart%22%20class%3D%22marker%20flowchart%22%20viewBox%3D%220%200%2010%2010%22%20refX%3D%22-1%22%20refY%3D%225%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Ccircle%20cx%3D%225%22%20cy%3D%225%22%20r%3D%225%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fcircle%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-crossEnd%22%20class%3D%22marker%20cross%20flowchart%22%20viewBox%3D%220%200%2011%2011%22%20refX%3D%2212%22%20refY%3D%225.2%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%201%2C1%20l%209%2C9%20M%2010%2C1%20l%20-9%2C9%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%202%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-crossStart%22%20class%3D%22marker%20cross%20flowchart%22%20viewBox%3D%220%200%2011%2011%22%20refX%3D%22-1%22%20refY%3D%225.2%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%201%2C1%20l%209%2C9%20M%2010%2C1%20l%20-9%2C9%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%202%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3Cg%20class%3D%22root%22%3E%3Cg%20class%3D%22clusters%22%3E%3C%2Fg%3E%3Cg%20class%3D%22edgePaths%22%3E%3Cpath%20d%3D%22M190.979%2C112.317L195.146%2C112.317C199.312%2C112.317%2C207.646%2C112.317%2C215.096%2C112.317C222.546%2C112.317%2C229.112%2C112.317%2C232.396%2C112.317L235.679%2C112.317%22%20id%3D%22L-A-B-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-A%20LE-B%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M345.412%2C112.317L349.578%2C112.317C353.745%2C112.317%2C362.078%2C112.317%2C369.612%2C112.383C377.145%2C112.449%2C383.879%2C112.581%2C387.246%2C112.647L390.613%2C112.713%22%20id%3D%22L-B-C-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-B%20LE-C%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M620.546%2C112.817L624.63%2C112.734C628.713%2C112.651%2C636.88%2C112.484%2C644.246%2C112.401C651.613%2C112.317%2C658.18%2C112.317%2C661.463%2C112.317L664.746%2C112.317%22%20id%3D%22L-C-D-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-C%20LE-D%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M873.958%2C112.317L878.125%2C112.317C882.291%2C112.317%2C890.625%2C112.317%2C898.075%2C112.317C905.525%2C112.317%2C912.091%2C112.317%2C915.375%2C112.317L918.658%2C112.317%22%20id%3D%22L-D-E-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-D%20LE-E%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M1086.947%2C92.824L1092.144%2C91.531C1097.342%2C90.239%2C1107.736%2C87.655%2C1116.216%2C86.363C1124.697%2C85.07%2C1131.264%2C85.07%2C1134.547%2C85.07L1137.83%2C85.07%22%20id%3D%22L-E-F-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-E%20LE-F%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M1222.706%2C74.239L1229.54%2C72.378C1236.373%2C70.518%2C1250.041%2C66.797%2C1262.825%2C64.937C1275.609%2C63.077%2C1287.509%2C63.077%2C1293.46%2C63.077L1299.41%2C63.077%22%20id%3D%22L-F-G-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-F%20LE-G%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M1218.314%2C104.564L1225.88%2C108.731C1233.445%2C112.897%2C1248.577%2C121.231%2C1264.792%2C127.84C1281.007%2C134.449%2C1298.306%2C139.333%2C1306.956%2C141.776L1315.605%2C144.218%22%20id%3D%22L-F-H-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-F%20LE-H%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M1320.706%2C163.359L1311.206%2C164.934C1301.707%2C166.508%2C1282.707%2C169.658%2C1259.743%2C171.233C1236.778%2C172.808%2C1209.848%2C172.808%2C1185.585%2C172.808C1161.322%2C172.808%2C1139.726%2C172.808%2C1117.323%2C166.402C1094.92%2C159.996%2C1071.71%2C147.184%2C1060.105%2C140.778L1048.499%2C134.372%22%20id%3D%22L-H-E-0%22%20class%3D%22%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%20LS-H%20LE-E%22%20style%3D%22fill%3Anone%3B%22%20marker-end%3D%22url(%23mermaid-908164f6-4902-4670-861f-d89f7c52a5df_flowchart-pointEnd)%22%3E%3C%2Fpath%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabels%22%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(0%2C%200)%22%3E%3CforeignObject%20width%3D%220%22%20height%3D%220%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(0%2C%200)%22%3E%3CforeignObject%20width%3D%220%22%20height%3D%220%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(0%2C%200)%22%3E%3CforeignObject%20width%3D%220%22%20height%3D%220%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(0%2C%200)%22%3E%3CforeignObject%20width%3D%220%22%20height%3D%220%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(0%2C%200)%22%3E%3CforeignObject%20width%3D%220%22%20height%3D%220%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%20transform%3D%22translate(1263.7079334259033%2C%2063.076677322387695)%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(-16.002099990844727%2C%20-11.993697166442871)%22%3E%3CforeignObject%20width%3D%2232.00419998168945%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%E9%80%9A%E8%BF%87%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%20transform%3D%22translate(1263.7079334259033%2C%20129.56407070159912)%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(-16.002099990844727%2C%20-11.993697166442871)%22%3E%3CforeignObject%20width%3D%2232.00419998168945%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%E5%A4%B1%E8%B4%A5%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20transform%3D%22translate(0%2C%200)%22%3E%3CforeignObject%20width%3D%220%22%20height%3D%220%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22edgeLabel%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22nodes%22%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-A-16%22%20data-node%3D%22true%22%20data-id%3D%22A%22%20transform%3D%22translate(95.48949432373047%2C%20112.31722259521484)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20rx%3D%220%22%20ry%3D%220%22%20x%3D%22-95.48949432373047%22%20y%3D%22-19.49369716644287%22%20width%3D%22190.97898864746094%22%20height%3D%2238.98739433288574%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-87.98949432373047%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%22175.97898864746094%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3E%E7%94%A8%E6%88%B7%E8%BE%93%E5%85%A5%EF%BC%9A%E6%95%B4%E6%AE%B5%E4%B8%AD%E6%96%87%E5%89%A7%E6%9C%AC%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-B-17%22%20data-node%3D%22true%22%20data-id%3D%22B%22%20transform%3D%22translate(293.19537353515625%2C%20112.31722259521484)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20rx%3D%225%22%20ry%3D%225%22%20x%3D%22-52.21638488769531%22%20y%3D%22-19.49369716644287%22%20width%3D%22104.43276977539062%22%20height%3D%2238.98739433288574%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-44.71638488769531%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%2289.43276977539062%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3EParser%20Agent%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-C-19%22%20data-node%3D%22true%22%20data-id%3D%22C%22%20transform%3D%22translate(507.7289810180664%2C%20112.31722259521484)%22%3E%3Cpolygon%20points%3D%22112.31722164154053%2C0%20224.63444328308105%2C-112.31722164154053%20112.31722164154053%2C-224.63444328308105%200%2C-112.31722164154053%22%20class%3D%22label-container%22%20transform%3D%22translate(-112.31722164154053%2C112.31722164154053)%22%20style%3D%22%22%3E%3C%2Fpolygon%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-85.32352447509766%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%22170.6470489501953%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3ETemporal%20Planner%20Agent%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-D-21%22%20data-node%3D%22true%22%20data-id%3D%22D%22%20transform%3D%22translate(772.002082824707%2C%20112.31722259521484)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20rx%3D%220%22%20ry%3D%220%22%20x%3D%22-101.95587921142578%22%20y%3D%22-19.49369716644287%22%20width%3D%22203.91175842285156%22%20height%3D%2238.98739433288574%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-94.45587921142578%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%22188.91175842285156%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3EContinuity%20Guardian%20Agent%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-E-23%22%20data-node%3D%22true%22%20data-id%3D%22E%22%20transform%3D%22translate(1008.5440826416016%2C%20112.31722259521484)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20rx%3D%220%22%20ry%3D%220%22%20x%3D%22-84.58612060546875%22%20y%3D%22-19.49369716644287%22%20width%3D%22169.1722412109375%22%20height%3D%2238.98739433288574%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-77.08612060546875%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%22154.1722412109375%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3EShot%20Generator%20Agent%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-F-25%22%20data-node%3D%22true%22%20data-id%3D%22F%22%20transform%3D%22translate(1182.9180183410645%2C%2085.07037448883057)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20rx%3D%220%22%20ry%3D%220%22%20x%3D%22-39.78781509399414%22%20y%3D%22-19.49369716644287%22%20width%3D%2279.57563018798828%22%20height%3D%2238.98739433288574%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-32.28781509399414%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%2264.57563018798828%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3EQA%20Agent%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-G-27%22%20data-node%3D%22true%22%20data-id%3D%22G%22%20transform%3D%22translate(1360.2037239074707%2C%2063.076677322387695)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20rx%3D%220%22%20ry%3D%220%22%20x%3D%22-55.493690490722656%22%20y%3D%22-19.49369716644287%22%20width%3D%22110.98738098144531%22%20height%3D%2238.98739433288574%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-47.993690490722656%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%2295.98738098144531%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3E%E8%BE%93%E5%87%BA%E5%88%86%E9%95%9C%E5%BA%8F%E5%88%97%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%20default%20flowchart-label%22%20id%3D%22flowchart-H-29%22%20data-node%3D%22true%22%20data-id%3D%22H%22%20transform%3D%22translate(1360.2037239074707%2C%20156.8109188079834)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20rx%3D%220%22%20ry%3D%220%22%20x%3D%22-39.49789810180664%22%20y%3D%22-19.49369716644287%22%20width%3D%2278.99579620361328%22%20height%3D%2238.98739433288574%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate(-31.99789810180664%2C%20-11.993697166442871)%22%3E%3Crect%3E%3C%2Frect%3E%3CforeignObject%20width%3D%2263.99579620361328%22%20height%3D%2223.987394332885742%22%3E%3Cdiv%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxhtml%22%20style%3D%22display%3A%20inline-block%3B%20white-space%3A%20nowrap%3B%22%3E%3Cspan%20class%3D%22nodeLabel%22%3E%E5%B1%80%E9%83%A8%E9%87%8D%E8%AF%95%3C%2Fspan%3E%3C%2Fdiv%3E%3C%2FforeignObject%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E)

- **智能剧本解析**：自动识别场景、对话和动作指令，支持自然语言和JSON格式
- **精准时序规划**：按短视频粒度智能切分内容，优化叙事节奏
- **连续性守护**：确保相邻分镜间角色状态、场景和情节的一致性
- **高质量分镜生成**：生成详细的中文画面描述和英文AI提示词，包含镜头角度、角色状态等
- **多模型支持**：兼容OpenAI、Qwen、DeepSeek、Ollama等多种AI提供商
- **自动重试机制**：请求失败时自动重试，提高系统稳定性
- **质量审查**：自动检查分镜质量和连续性问题，提供优化建议

## 技术架构

项目采用多智能体协作架构，基于以下技术栈：

- **Python 3.10+**：核心开发语言
- **FastAPI**：高性能Web框架
- **LangChain + LangGraph**：工作流编排和智能体管理
- **多模型支持**：兼容OpenAI、Qwen、DeepSeek、Ollama等
- **Pydantic**：数据验证和设置管理
- **环境变量配置**：灵活的配置管理

## 快速上手

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/HengLine/tool-storyboard-agent.git
cd tool-storyboard-agent

# 直接运行，自动创建虚拟环境
python .\start_app.py

# 或者手动创建虚拟环境
    python -m venv .venv
    # 激活虚拟环境 (Windows)
    .venv\Scripts\activate
    # 激活虚拟环境 (Linux/Mac)
    source .venv/bin/activate
    # 安装依赖
    pip install -r requirements.txt
```

### 2. 配置设置

复制配置文件并设置环境变量：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的参数：

```properties
# 选择AI提供商：openai, qwen, deepseek, ollama
AI_PROVIDER=qwen

# 根据选择的提供商配置对应的API密钥
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://api.example.com/v1

# 或 OPENAI_API_KEY=your_openai_api_key
# 或 DEEPSEEK_API_KEY=your_deepseek_api_key

# 可选：设置超时时间和重试次数
AI_API_TIMEOUT=60
AI_RETRY_COUNT=3
```

### 3. 启动应用

```bash
python start_app.py
```

应用将在 `http://0.0.0.0:8000` 启动，提供API接口服务。



## 使用方法

### 1. 作为Python库使用

```python
from hengline.generate_agent import generate_storyboard

# 基本使用：传入中文剧本文本
script_text = """
场景：咖啡馆内
小明坐在窗边，看着窗外的雨。
小红：你看起来心情不太好。
小明：嗯，工作上遇到了一些问题。
小红：别担心，一切都会好起来的。
"""

# 生成分镜
result = generate_storyboard(script_text)
print(f"生成了 {result['total_shots']} 个分镜")
for shot in result['shots']:
    print(f"\n分镜 {shot['shot_id']}:")
    print(f"时间: {shot['start_time']}-{shot['end_time']}s")
    print(f"描述: {shot['description']}")
```

### 2. API接口调用

启动服务后，可以通过HTTP接口调用：

```bash
curl -X POST http://localhost:8000/api/generate_storyboard \
  -H "Content-Type: application/json" \
  -d '{"script_text": "场景：咖啡馆内\n小明坐在窗边...", "style": "realistic"}'
```

### 3. 集成到其他系统

#### 集成到Web应用

```python
# Flask示例
from flask import Flask, request, jsonify
from hengline.generate_agent import generate_storyboard

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    result = generate_storyboard(
        script_text=data['script_text'],
        style=data.get('style', 'realistic')
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
```

#### 集成到LangChain工作流

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from hengline.client.client_factory import get_ai_client

# 获取配置的AI客户端
llm = get_ai_client()

# 创建LangChain链
prompt = PromptTemplate(
    input_variables=["story"],
    template="总结这个故事：{story}"
)
chain = LLMChain(llm=llm, prompt=prompt)

# 使用链
result = chain.run(story="小明和小红在咖啡馆的对话...")
print(result)
```

#### 集成到A2A系统

```python
# A2A Agent示例
from a2a import Agent, Message
from hengline.generate_agent import generate_storyboard

class StoryboardAgent(Agent):
    def process_message(self, message: Message) -> Message:
        # 处理传入的剧本消息
        script = message.content
        storyboard = generate_storyboard(script)
        
        # 返回分镜结果
        return Message(
            content=storyboard,
            type="storyboard_result"
        )

# 注册和使用Agent
agent = StoryboardAgent(name="storyboard_agent")
```

## 输入输出

```python
# 自定义风格和时长
result = generate_storyboard(
    script_text,
    style="cinematic",  # 可选: realistic, anime, cinematic, cartoon
    duration_per_shot=8,  # 每段目标时长（秒）
    prev_continuity_state=None  # 用于长剧本续生成
)
```

生成的分镜结果为结构化JSON，包含以下核心字段：

```json
{
  "total_shots": 3,              // 生成的分镜总数
  "storyboard_title": "咖啡馆对话", // 分镜标题
  "shots": [
    {
      "shot_id": "shot_001",    // 分镜ID
      "start_time": 0.0,         // 开始时间（秒）
      "end_time": 5.0,           // 结束时间（秒）
      "duration": 5.0,           // 分镜时长
      "description": "小明坐在咖啡馆窗边...", // 中文画面描述
      "prompt_en": "A man sitting by the window...", // 英文AI提示词
      "characters": ["小明"],    // 角色列表
      "dialogue": "",           // 对话内容
      "camera_angle": "medium shot", // 镜头角度
      "continuity_anchors": ["小明位置:窗边", "天气:下雨"] // 连续性锚点
    },
    // 更多分镜...
  ],
  "status": "success",          // 生成状态
  "warnings": []                 // 警告信息
}
```



## 配置说明

系统配置支持两种方式：配置文件和环境变量（优先级更高）。

### 环境变量配置

关键环境变量：

| 环境变量 | 说明 | 默认值 |
|---------|------|-------|
| AI_PROVIDER | AI提供商名称（openai/qwen/deepseek/ollama） | openai |
| OPENAI_API_KEY | OpenAI API密钥 | - |
| QWEN_API_KEY | 文心一言API密钥 | - |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | - |
| AI_API_TIMEOUT | API请求超时时间（秒） | 60 |
| AI_RETRY_COUNT | 请求失败重试次数 | 3 |
| AI_TEMPERATURE | 生成温度参数 | 0.7 |
| AI_MAX_TOKENS | 最大生成令牌数 | 2000 |

### 配置文件

`config/config.json` 包含默认配置，可通过环境变量覆盖。

## 实际应用场景

### 短视频内容创作
- 将小说章节转换为短视频分镜脚本
- 为广告创意生成详细的镜头规划
- 自动将剧本拆分为社交媒体短视频格式

### 影视前期制作辅助
- 快速生成剧本的视觉化预览
- 辅助导演进行镜头规划和调度
- 为分镜头绘制提供详细参考

### 教育培训应用
- 为教学内容创建情景化视频脚本
- 将复杂概念通过分镜形式直观呈现
- 辅助培训视频的标准化制作

## 最佳实践

1. **剧本格式优化**
   - 使用明确的场景标识和角色对白格式
   - 避免过于冗长的描述，保持每个场景的焦点
   - 为重要动作和情感变化添加明确标记

2. **参数调优**
   - 对于对话密集型内容，可适当延长`duration_per_shot`
   - 情感细腻的场景推荐使用`cinematic`风格
   - 动作场景可选择`realistic`风格获得更准确的描述

3. **性能优化**
   - 对于长剧本，建议分段处理并使用`prev_continuity_state`保持连贯性
   - 根据服务器资源调整`AI_RETRY_COUNT`参数
   - 生产环境中推荐使用`gpt-4o`或同等性能模型

## 故障排除

### 常见问题及解决方案

1. **API密钥错误**
   - 检查环境变量中的API密钥是否正确设置
   - 确保密钥未过期，并有足够的使用额度
   - 验证AI_PROVIDER与密钥类型是否匹配

2. **分镜生成失败**
   - 检查剧本格式是否规范，尝试简化复杂描述
   - 增加`AI_RETRY_COUNT`参数值
   - 查看日志文件获取详细错误信息

3. **连续性问题**
   - 确保相邻场景描述包含足够的上下文信息
   - 对于长剧本，使用分段处理并传递连续性状态
   - 检查`continuity_anchors`字段是否正确捕获关键信息

4. **性能问题**
   - 降低模型温度参数可提高响应速度
   - 减少单次处理的剧本长度
   - 优化系统资源分配

## 许可证

MIT License

## 贡献指南

欢迎提交Issue和Pull Request！贡献前请确保：

1. 遵循现有代码风格和架构
2. 为新功能添加适当的测试用例
3. 更新相关文档

## 联系方式

如有问题或建议，请提交GitHub Issue或联系项目维护团队。