# 抖音数据采集操作手册

## 前置

- 使用浏览器自动化 skill（`browser-use-automation`，`computer_use_tool` plane="bu"，`import aha_browser_use as bu`）。
- 抖音网页版免登录可看主页与视频详情；遇登录墙/验证码按浏览器 skill 的授权规则处理（`interaction.request_action` type="browserControl"），不绕过。

## 1. 解析链接

短链 `v.douyin.com/xxx`：

- 用 curl/Invoke-WebRequest 跟随重定向拿最终 URL（Windows 用 `curl.exe -s -L -o NUL -w "%{url_effective}"`）。
- 重定向到 `/share/user/<sec_uid>` = 用户主页；`/video/<aweme_id>` 或 `?modal_id=<aweme_id>` = 视频页。
- 记录 sec_uid / aweme_id，后续全部请求基于它们。

## 2. 主页采集

- `bu.navigate("https://www.douyin.com/user/<sec_uid>")`，`bu.wait_for_load`。
- 读取：粉丝/获赞/关注、抖音号、IP 属地、简介、作品 tab 数、合集信息、置顶条（"Tag: 置顶"）。
- 作品网格滚动加载：循环 `bu.snapshot(within="viewport", view="all")` + `bu.scroll`，提取每屏 `img` 的 alt（标题）与邻近 `text` 数字（点赞数），去重收集。
- 网格中置顶视频可能无 `<a>` 链接，用 `bu.find(标题)` 拿 href。

## 3. 视频详情采集

- `bu.navigate("https://www.douyin.com/video/<aweme_id>")`。
- 读取：点赞/评论/收藏/转发、时长（video 元素 `duration`）、合集与集数、标签、发布时间。
- 网页版不显示播放量：以点赞为热度主指标，按知识类 3-6% 点赞率估算播放量并标注"估算"。

## 4. 画面帧采集

- `bu.js` 获取 video 元数据（duration/width/height）。
- 逐时间点截帧：JS 设置 `currentTime` + `play`，等待约 2 秒，`bu.screenshot(tag=...)`。
- 至少 5 帧：开场 1-3s / 标题卡 5s / 中段 40% / 高潮 60% / 结尾 95%。
- 用截图观察描述 + OCR 记录画面元素、字幕、动效。

## 5. 旁白文案

- `video_search` 按"博主名 + 视频标题关键词"搜索，snippet 用 full 模式拿全文。
- 转载/复刻视频常含原片完整旁白，可交叉验证；引用时注明来源为搜索返回。

## 6. 结构化输出

整理为：profile 字段 / 作品表（标题+点赞）/ 单视频详情（互动+时长+合集+标签）/ 帧清单（时间点+画面描述）/ 旁白全文，供拆解报告使用。

## 数据口径

- 互动数字以采集时页面显示为准，注明采集日期。
- 估算值一律标注"估算"，不用估算冒充官方数据。
