#!/usr/bin/env python3
"""
Extract real user messages from Claude Code session transcript jsonl files.

不受 /compact 影响——transcript jsonl 是磁盘上的原始会话记录，
compact 只压缩 LLM 上下文窗口，不动磁盘文件。所以提取 jsonl 能拿到
compact 之前被"忘掉"的完整用户输入。

用法（本 skill 第一步就是跑它）:
  python extract_transcript.py                              # 自动发现当前 cwd 全部 jsonl，按时间过滤保留最近 24h
  python extract_transcript.py --all                        # 该 cwd 所有 jsonl，仍按时间过滤保留最近 24h
  python extract_transcript.py --n 5                        # 最近 5 个 jsonl，仍按时间过滤保留最近 24h
  python extract_transcript.py <path.jsonl>                # 指定单文件，仍按时间过滤保留最近 24h
  python extract_transcript.py --out <file>                 # 输出到文件（默认 stdout）
  python extract_transcript.py --hours 48                   # 放宽到最近 48 小时
  python extract_transcript.py --hours 0                    # 关闭时间过滤，取全部历史（跨天全量审计才用）

输出 markdown：每条用户消息一节 `## [timestamp]\n\n<content>\n`。
过滤掉非用户真实输入：tool_result 块、<system-reminder> 注入、
<command-message>/<command-name>/<local-command-stdout> 注入、task-notification。
用户调用的 slash command 只保留命令名 + 参数作为意图线索，skill body 跳过。
默认只保留最近 24 小时的消息（收尾审计聚焦本次会话，不扫历史全量）；
--hours 0 关闭时间过滤。无法解析 timestamp 的消息保守保留（不误删当前会话）。

需求状态追踪（本会话已解决 vs 待处理）：
对标记为"需求"的消息，检测后续是否有确认/否定/转移的信号，标注：
  - 已解决 ✅：后续有正面确认（"不错""完美""给你👍"等）
  - 已解决 ✅（用户取消）：后续有否定词（"不需要""不用""下次再说"等）
  - 待处理 ⏳：无确认信号
跨会话状态由 requirement_ledger.json 持久化（默认 ~/.claude/state/），
本次会话内检测独立于 ledger。
已解决/已取消的需求默认折叠——只在「需求状态概览」段显示数字，不逐条列全文
（回顾审计真正需要看的是 ⏳待处理 和非需求类消息）。用 --show-resolved 恢复完整输出。
缓存（避免短时间重复提取）：
neat-freak 跑完紧接着跑 self-improving-agent 时（或反过来），从头读一遍 jsonl 是浪费。
脚本默认带 30 分钟缓存：jsonl 文件列表相同 + TTL 未过 → 直接复用上次输出。
不查 mtime/size——会话进行中每次 tool call 都让 jsonl 增长，查了就永不命中；
增长带来的新内容（skill 执行日志、tool result）本就被 isMeta/isSidechain 过滤。
用 --no-cache 强制重新提取，--cache-ttl N 调有效期（分钟），--cache-check-content 开严格模式（查 mtime/size，确保数据真没变）。

跨会话未闭环需求（ledger 的核心产出）：
一条需求若在**更早的会话**里被提出、至今仍是 ⏳待处理，就是用户 CLAUDE.md
「需求闭环」铁律里的「被顶掉」事故——单靠会话内检测永远看不见，因为提出它的
那个 jsonl 早已不在 24h 时间窗内。ledger 按需求文本哈希跨会话累计，每次运行
输出「跨会话未闭环需求」段。

  python extract_transcript.py --no-ledger                   # 不读写 ledger
  python extract_transcript.py --ledger <path.json>           # 指定 ledger 路径

# Version: 1.1.0 (2026-09-10) —— 实现此前只在文档字符串里承诺过的 requirement_ledger.json
# Version: 1.0.0 (2026-09-01)
"""
# 架构：本文件是唯一真实实现；neat-freak/scripts/ 与 self-improving-agent/scripts/
# 下的 extract_transcript.py 都是 20 行薄壳，用 exec() 指向本文件。改本文件即可，
# 两份 skill 自动同步，无版本漂移。
import json
import sys
import os
import glob
import re
import hashlib
import argparse
from datetime import datetime, timedelta, timezone

# GBK terminal-safe: force utf-8 stdout (Windows GBK can't encode ✅ etc).
# Per CLAUDE.md "GBK 编码坑" — scripts printing Chinese/emoji must reconfigure.
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def sanitize_cwd(p):
    """C:\\Users\\kuang -> C--Users-kuang（Claude Code projects 目录转义规则：冒号和斜杠都替换为横线，不是删除冒号）"""
    return p.replace(':', '-').replace('\\', '-').replace('/', '-')


def parse_ts(ts):
    """解析 ISO timestamp（Claude Code 格式如 2026-08-31T14:23:45.123Z），返回 aware datetime 或 None。

    解析失败返回 None——调用方对 None 保守保留（不误删当前会话里偶发无 timestamp 的消息）。
    """
    if not ts or not isinstance(ts, str):
        return None
    try:
        s = ts.strip().replace('Z', '+00:00')
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _extract_command_intent(text):
    """从 <command-message> 块提取命令名 + 参数（保留意图，跳过 skill body）"""
    name_m = re.search(r'<command-name>([^<]+)</command-name>', text)
    args_m = re.search(r'<command-args>([^<]*)</command-args>', text)
    parts = []
    if name_m:
        parts.append(name_m.group(1).strip())
    if args_m and args_m.group(1).strip():
        parts.append('参数: ' + args_m.group(1).strip())
    return ' | '.join(parts) if parts else None


# 轻量分类标记（规则关键词，不调 LLM）。优先级：纠正 > 踩坑 > 需求 > 偏好。
# 是回顾时的线索，不是定论——误标可接受。
_CATEGORY_RULES = [
    ('纠正', ('不要问', '不要说', '别再', '错了', '不是这个', '我说的是', '为什么还',
              '为什么', '停下来', '打断', '不对', '不需要', '不是说了', '为什么还要')),
    ('踩坑', ('报错', '失败', '超时', '不行', '卡住', '崩溃', 'error', '异常', '没成功', '翻车')),
    ('需求', ('优化', '加', '改', '做', '请', '帮我', '能不能', '要求',
              '保存', '删除', '备份', '加入', '更新', '升级')),
    ('偏好', ('以后都', '永远', '默认', '喜欢', '习惯', '每次都', '一律')),
]
# 收尾噪声词：短消息含这些词 = 纯推进/完成度问答，回顾时折叠不逐条列。
# 单字词只做精确匹配（整个消息就是这个字），多字词用子串匹配。
_NOISE_WORDS = ('搞定', '确认', '清', '收到', '处理了', '完成', '继续', '好了', '可以了',
                '明白', '了解', 'ok', 'done', '是的', '对', '好', '嗯', '行',
                '已经处理', '全部搞定', '搞定完', '了吗', '处理完')
# 需求解决信号（后续消息出现这些词 = 前面的需求已被确认完成）。
_RESOLUTION_SIGNALS = (
    '好了', '可以了', '搞定', '不错', '完美', '很好', 'ok', 'done', '行',
    '可以', '没了', '就这样', '先这样', '暂时够了', '就这样吧', '对', '是的',
    '处理了', '已经处理', '全部搞定', '搞定完', '处理完',
    '给你', '👍', '🎉', '👏',
)
# 用户主动取消信号："下次再做""不需要"= 需求不执行，也归为"已解决"但不算完成。
_RESOLUTION_CANCEL = (
    '不需要', '不用', '下次再说', '先不做', '不用了', '算了',
    '下次再做', '以后再', '暂时不',
)


def classify(text):
    """规则关键词分类，返回类别名或 None。优先级纠正>踩坑>需求>偏好。"""
    low = text.lower() if text else ''
    for cat, words in _CATEGORY_RULES:
        for w in words:
            if w in low:
                return cat
    return None


def is_noise(text):
    """短消息（<20 字）+ 收尾/完成度词 = 回顾噪声，默认折叠。长消息有实质不过滤。
    单字词只做精确匹配（防"好的"被"好"误命中），多字词用子串匹配。
    """
    s = text.strip()
    if not s or len(s) >= 20:
        return False
    low = s.lower()
    for w in _NOISE_WORDS:
        if len(w) == 1:
            if low == w:
                return True
        elif w in low:
            return True
    return False


def _detect_requirement_status(msgs):
    """对标记为「需求」的消息，检测后续是否有确认/取消信号，返回 (ts, txt, cat, status) 列表。

    status:
      - '✅已解决'   后续消息含 _RESOLUTION_SIGNALS 词
      - '❌已取消'   后续消息含 _RESOLUTION_CANCEL 词
      - '⏳待处理'   无信号（未在本会话内确认完成或取消）

    设计要点：
    - 只看后续消息，不回看前文（前文无关）
    - 窗口限制 20 条：防止跨无关话题误匹配（用户聊别的事时恰好出现"好了"不该标记前面需求）
    - 跳过同为「需求」类的中间消息：两条需求连发不代表前一条被解决了
    - 跳过噪声：is_noise() 为 True 的短消息不算作确认（"行""ok"等单字本身既是需求内容也是噪声）
    """
    result = []
    n = len(msgs)
    for i, (ts, txt, cat) in enumerate(msgs):
        if cat != '需求':
            result.append((ts, txt, cat, None))
            continue
        status = '⏳待处理'
        for j in range(i + 1, min(i + 21, n)):  # 窗口 20 条
            _, future_txt, future_cat = msgs[j]
            # 跳过同为需求类的中间消息（需求连发不算解决）
            if future_cat == '需求':
                continue
            # 跳过纯噪声短消息
            if is_noise(future_txt):
                continue
            low = future_txt.lower()
            # 先检查取消信号（优先级更高：取消后不必再等确认）
            for w in _RESOLUTION_CANCEL:
                if w in low:
                    status = '❌已取消'
                    break
            if status != '⏳待处理':
                break
            for w in _RESOLUTION_SIGNALS:
                if w in low:
                    status = '✅已解决'
                    break
            if status != '⏳待处理':
                break
        result.append((ts, txt, cat, status))
    return result


def extract_user_msgs(path):
    """从单个 jsonl 提取真实用户消息 [(timestamp, text, category)]"""
    msgs = []
    if not os.path.exists(path):
        return msgs
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get('type') != 'user':
                continue
            # 跳过 sidechain / meta 注入（skill body 全文、subagent 对话等系统注入）。
            # 真实用户主对话消息 isSidechain=False / isMeta 缺失；系统注入为 True。
            # 这是过滤 skill body 污染的最可靠标志（标签检测会漏，因为注入是纯文本无 <command-message> 标签）。
            if d.get('isSidechain') is True or d.get('isMeta') is True:
                continue
            c = d.get('message', {}).get('content')
            txt = None
            if isinstance(c, str):
                txt = c
            elif isinstance(c, list):
                # 用户消息里的 tool_result 块 = 工具返回，不是用户输入，整条跳过
                if any(isinstance(b, dict) and b.get('type') == 'tool_result' for b in c):
                    continue
                texts = [b.get('text', '') for b in c
                         if isinstance(b, dict) and b.get('type') == 'text']
                if texts:
                    txt = '\n'.join(texts)
            if not txt:
                continue
            s = txt.strip()
            if not s:
                continue
            ts = d.get('timestamp', '')
            # 系统注入块：不是用户真实输入
            if s.startswith('<system-reminder>'):
                continue
            if s.startswith('<local-command-stdout>'):
                continue
            if s.startswith('[SYSTEM NOTIFICATION') or 'NOT USER INPUT' in s:
                continue
            # task-notification（后台任务完成通知）
            if s.startswith('<task-notification>') or 'task-notification' in s[:40].lower():
                continue
            # /compact 自动总结块（非用户真实输入）：type=user + isSidechain=False +
            # isMeta 缺失，能绕过上面的 sidechain/meta 过滤，但 content 以固定模板开头。
            # 不过滤会被当"用户消息"提取，单条 17-20KB 虚增输出且污染需求完成度审计。
            # neat-freak 审计发现（2026-08-31，nf-transcript.md 96 条里约 8 条是 compact summary）。
            if s.startswith('This session is being continued from a previous conversation'):
                continue
            # slash command 调用注入：content 里混有 <command-message>/<command-name> 标签 + skill body。
            # 标签常在文本中间（前面有 "Base directory for this skill:..." 等），用 in 检测而非 startswith。
            if '<command-message>' in s or '<command-name>' in s or '<command-args>' in s:
                intent = _extract_command_intent(s)
                if intent:
                    msgs.append((ts, '[用户调用命令] ' + intent, classify('[用户调用命令] ' + intent)))
                continue
            msgs.append((ts, s, classify(s)))
    return msgs


def discover_jsonl(n=None):
    """自动发现当前 cwd 的会话 jsonl，按 mtime 倒序。找不到当前 cwd 目录则 fallback 扫所有 projects 子目录。"""
    home = os.path.expanduser('~')
    cwd = os.getcwd()
    # 1. 优先当前 cwd 转义目录
    target_dir = os.path.join(home, '.claude', 'projects', sanitize_cwd(cwd))
    files = glob.glob(os.path.join(target_dir, '*.jsonl'))
    # 2. fallback：当前 cwd 目录没 jsonl（如 cwd 转义规则不符），扫所有 projects/*/ 子目录取最近
    if not files:
        files = glob.glob(os.path.join(home, '.claude', 'projects', '*', '*.jsonl'))
    files.sort(key=os.path.getmtime, reverse=True)
    if n is not None:
        files = files[:n]
    return files


_TERMINAL_STATUS = ('✅已解决', '❌已取消')
LEDGER_VERSION = 1
LEDGER_MAX_ITEMS = 500
LEDGER_PRUNE_DAYS = 60


def default_ledger_path():
    """~/.claude/state/requirement_ledger.json

    放在 ~/.claude/state/ 而不是 skills/ 下：ledger 是可再生的派生状态，不属于
    skill 资产（skills/ 要能原样分发到 kuang-skills 公开仓）。
    """
    return os.path.join(os.path.expanduser('~'), '.claude', 'state', 'requirement_ledger.json')


def _req_key(txt):
    """需求文本 → 稳定短哈希（跨会话、跨 jsonl 同一条需求得到同一把钥匙）。"""
    norm = re.sub(r'\s+', '', txt or '')[0:120]
    return hashlib.sha1(norm.encode('utf-8')).hexdigest()[:16]


def update_ledger(path, kept, src_of):
    """把本次会话的需求状态并入 ledger，返回「跨会话未闭环」条目列表。

    为什么需要它：会话内检测（_detect_requirement_status）只能看到本次跑到的消息。
    一条需求若在 7 天前的会话提出、从未闭环，那个 jsonl 早已被 --hours 24 过滤掉，
    会话内检测永远不会再看见它 → 这类「被顶掉」需求（用户 CLAUDE.md 定义为最严重的
    执行事故）成了盲区。ledger 按文本哈希跨会话累计，把盲区变成可机检输出。

    src_of: {(ts, txt[:80]): jsonl 文件名}，用来判定「这条需求属于哪个会话」。
    **不能用 discover_jsonl() 的文件列表当会话身份**——该列表不随时间窗变化
    （--hours 只过滤消息、不过滤文件），拿它当 cur_sessions 会让跨会话检测永远失效：
    两次运行的文件列表完全相同 → "others" 恒为空。必须用真正产出了保留消息的会话。

    状态单调性：已解决/已取消是终态，后续重跑或重复出现不会把它降级回 ⏳待处理。

    已知限制：ledger 只能记住它被运行之后见过的需求。首次使用时可对该项目跑一次
    `--hours 0` 把历史需求灌进 ledger，之后 24h 窗口的常规运行才有对照基线。
    """
    now_iso = datetime.now(timezone.utc).isoformat(timespec='seconds')
    cur_sessions = set()
    for ts, txt, cat, status in kept:
        if cat == '需求' and status:
            base = src_of.get((ts, txt[:80]))
            if base:
                cur_sessions.add(base)
    items = {}
    try:
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get('items'), dict):
            items = data['items']
    except Exception:
        items = {}  # 首次运行 / 文件损坏 → 从空 ledger 重建，不阻塞提取

    for ts, txt, cat, status in kept:
        if cat != '需求' or not status:
            continue
        key = _req_key(txt)
        it = items.get(key)
        if not isinstance(it, dict):
            it = {'text': re.sub(r'\s+', ' ', txt.strip())[0:200],
                  'first_seen': ts, 'sessions': []}
        it['last_seen'] = ts
        base = src_of.get((ts, txt[:80]))
        if base and base not in it['sessions']:
            it['sessions'].append(base)
        del it['sessions'][10:]  # 只留最近 10 个来源会话，防无限增长
        prev = it.get('status')
        if status in _TERMINAL_STATUS or prev not in _TERMINAL_STATUS:
            it['status'] = status
        items[key] = it

    # 剪枝：终态且久未出现的条目不再有审计价值，避免 ledger 无限膨胀
    cutoff = datetime.now(timezone.utc) - timedelta(days=LEDGER_PRUNE_DAYS)
    pruned = {}
    for key, it in items.items():
        if not isinstance(it, dict):
            continue
        if it.get('status') in _TERMINAL_STATUS:
            dt = parse_ts(it.get('last_seen', ''))
            if dt is not None and dt < cutoff:
                continue
        pruned[key] = it
    if len(pruned) > LEDGER_MAX_ITEMS:
        # 超量时优先丢终态、保留仍开着的需求
        ordered = sorted(pruned.items(),
                         key=lambda kv: (kv[1].get('status') in _TERMINAL_STATUS,
                                         kv[1].get('last_seen', '')))
        pruned = dict(ordered[-LEDGER_MAX_ITEMS:])

    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump({'version': LEDGER_VERSION, 'updated_at': now_iso,
                       'items': pruned}, fh, ensure_ascii=False, indent=1)
    except OSError as e:
        sys.stderr.write(f'[warn] ledger 写入失败（不影响提取）: {e}\n')

    # 跨会话未闭环：仍是 ⏳ 且来源会话里有本次未参与的
    carry = []
    for it in pruned.values():
        if it.get('status') != '⏳待处理':
            continue
        others = [s for s in (it.get('sessions') or []) if s not in cur_sessions]
        if others:
            carry.append(it)
    carry.sort(key=lambda it: it.get('first_seen', ''))
    return carry


def default_cache_paths():
    """~/.claude/state/transcript_cache.json + .md

    缓存提取结果：neat-freak 跑完紧接着跑 self-improving-agent 时（或反过来），
    从头读一遍 jsonl 是浪费。默认按「jsonl 文件列表 + TTL」判新鲜度——不查 mtime/size，
    因为会话进行中每次 tool call（Read/Bash）都会让 jsonl 增长，mtime 一直在变，
    严格匹配等于永不命中。jsonl 增长带来的新内容（skill 执行日志、tool result）
    本来就被 isMeta/isSidechain 过滤，不影响输出质量。
    不区分调用方——谁先跑都写缓存，第二个跑的命中。
    """
    base = os.path.join(os.path.expanduser('~'), '.claude', 'state')
    return (os.path.join(base, 'transcript_cache.json'),
            os.path.join(base, 'transcript_cache.md'))


def check_cache(meta_path, output_path, args, files):
    """检查缓存是否新鲜。返回 (hit: bool, output: str or None)。

    命中条件全满足才复用（任一不满足就重新提取）：
    - 缓存文件存在且 TTL 未过
    - hours / show_resolved 参数匹配
    - jsonl 文件列表完全相同（没有新 session 的 jsonl 出现）
    默认不查 mtime/size（见上方说明）；--cache-check-content 开启严格模式才查。
    """
    try:
        with open(meta_path, encoding='utf-8') as f:
            meta = json.load(f)
    except Exception:
        return False, None
    generated = parse_ts(meta.get('generated_at'))
    if generated is None:
        return False, None
    if datetime.now(timezone.utc) - generated > timedelta(minutes=args.cache_ttl):
        return False, None
    if meta.get('hours') != args.hours:
        return False, None
    if meta.get('show_resolved') != args.show_resolved:
        return False, None
    cached_fps = meta.get('jsonl_fingerprints', {})
    if set(cached_fps.keys()) != set(files):
        return False, None
    if args.cache_check_content:
        for f in files:
            try:
                st = os.stat(f)
                cached = cached_fps.get(f, {})
                if int(st.st_mtime) != cached.get('mtime') or st.st_size != cached.get('size'):
                    return False, None
            except OSError:
                return False, None
    try:
        with open(output_path, encoding='utf-8') as f:
            output = f.read()
    except Exception:
        return False, None
    return True, output


def write_cache(meta_path, output_path, args, files, output):
    """写缓存元数据 + 输出。失败只 warn 不阻塞提取。"""
    fps = {}
    for f in files:
        try:
            st = os.stat(f)
            fps[f] = {'mtime': int(st.st_mtime), 'size': st.st_size}
        except OSError:
            pass
    meta = {
        'version': 1,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'hours': args.hours,
        'show_resolved': args.show_resolved,
        'jsonl_fingerprints': fps,
    }
    try:
        os.makedirs(os.path.dirname(os.path.abspath(meta_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    except OSError as e:
        sys.stderr.write(f'[warn] 缓存写入失败（不影响提取）: {e}\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('path', nargs='?', help='单个 jsonl 路径（不传则自动发现当前 cwd 的会话）')
    ap.add_argument('--n', type=int, default=None,
                    help='自动发现时取最近 N 个 jsonl，覆盖 compact 前后（默认 all）')
    ap.add_argument('--all', action='store_true', help='取该 cwd 所有 jsonl（仍受 --hours 时间过滤）')
    ap.add_argument('--hours', type=float, default=24.0,
                    help='只保留最近 N 小时的消息（默认 24，收尾审计聚焦本次会话）；0 关闭时间过滤取全部历史')
    ap.add_argument('--out', help='输出到文件（默认 stdout，中文多时建议写文件再 Read）')
    ap.add_argument('--ledger', default=None,
                    help='跨会话需求 ledger 路径（默认 ~/.claude/state/requirement_ledger.json）')
    ap.add_argument('--no-ledger', action='store_true',
                    help='不读写 ledger（纯只读提取，用于给别人看/敏感场景）')
    ap.add_argument('--show-resolved', action='store_true',
                    help='默认折叠已解决/已取消的需求（只在概览显示数字）。加此参数恢复逐条列出')
    ap.add_argument('--no-cache', action='store_true',
                    help='跳过缓存，强制重新提取')
    ap.add_argument('--cache-ttl', type=float, default=30.0,
                    help='缓存有效期（分钟，默认 30）。jsonl 文件列表相同 + TTL 未过 → 复用上次提取结果')
    ap.add_argument('--cache-check-content', action='store_true',
                    help='严格模式：不仅查文件列表，还查每个 jsonl 的 mtime/size。会话进行中 jsonl 持续增长会导致此模式几乎永不命中，仅用于确保数据真没变的场景')
    args = ap.parse_args()

    if args.path:
        files = [args.path]
    elif args.n is not None:
        files = discover_jsonl(n=args.n)
    else:
        files = discover_jsonl(n=None)  # 默认取全部 jsonl，24h 时间窗过滤

    if not files:
        sys.stderr.write('未找到任何 jsonl。检查 cwd 转义目录：'
                         + os.path.join(os.path.expanduser('~'),
                                        '.claude', 'projects', sanitize_cwd(os.getcwd()))
                         + '\n')
        sys.exit(1)

    # 缓存检查：短时间内重复跑（neat-freak → self-improving-agent 或反过来）时跳过重新提取。
    # 默认只查 TTL + 文件列表（不查 mtime/size）——会话进行中 jsonl 因 tool call 持续增长，
    # 查 mtime 等于永不命中。增长带来的新内容（skill 日志、tool result）被 isMeta/isSidechain 过滤。
    cache_meta_path, cache_output_path = default_cache_paths()
    if not args.no_cache:
        hit, cached = check_cache(cache_meta_path, cache_output_path, args, files)
        if hit:
            age_min = '未知'
            try:
                with open(cache_meta_path, encoding='utf-8') as f:
                    meta = json.load(f)
                g = parse_ts(meta.get('generated_at'))
                if g:
                    age_min = f'{(datetime.now(timezone.utc) - g).total_seconds() / 60:.1f}'
            except Exception:
                pass
            if args.out:
                with open(args.out, 'w', encoding='utf-8') as f:
                    f.write(cached)
                sys.stderr.write(f'[cache] 命中缓存（{age_min} 分钟前的结果，跳过重新提取），已写入 {args.out}\n')
            else:
                sys.stdout.write(cached)
            return

    all_msgs = []
    src_of = {}  # (ts, txt[:80]) -> jsonl basename，供 ledger 判定需求属于哪个会话
    for f in files:
        base = os.path.basename(f)
        for ts, txt, cat in extract_user_msgs(f):
            all_msgs.append((ts, txt, cat))
            src_of.setdefault((ts, txt[:80]), base)

    # 去重（timestamp + 内容前 80 字符，避免同一会话被读两次）
    seen = set()
    unique = []
    for ts, txt, cat in all_msgs:
        key = (ts, txt[:80])
        if key in seen:
            continue
        seen.add(key)
        unique.append((ts, txt, cat))

    # 时间过滤：只保留最近 --hours 小时的消息（收尾审计聚焦本次会话，不扫历史全量）。
    # cutoff=None 表示关闭过滤（--hours 0）。parse 失败的消息保守保留（不误删当前会话）。
    cutoff = None
    if args.hours and args.hours > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    kept = []
    dropped_by_time = 0
    for ts, txt, cat in unique:
        if cutoff is not None:
            dt = parse_ts(ts)
            if dt is not None and dt < cutoff:
                dropped_by_time += 1
                continue
        kept.append((ts, txt, cat))

    kept.sort(key=lambda x: x[0])
    kept = _detect_requirement_status(kept)

    # 跨会话需求 ledger（纯附加产物；异常绝不影响提取本身）
    carry = []
    ledger_path = None
    if not args.no_ledger:
        ledger_path = args.ledger or default_ledger_path()
        try:
            carry = update_ledger(ledger_path, kept, src_of)
        except Exception as e:
            sys.stderr.write(f'[warn] ledger 更新异常（不影响提取）: {e}\n')

    if cutoff is not None:
        window_desc = f'，时间窗最近 {args.hours:g} 小时（过滤掉 {dropped_by_time} 条更早消息）'
    else:
        window_desc = '，未开时间窗（全部历史）'

    # 分类统计（回顾清单的线索）
    cat_counts = {'纠正': 0, '踩坑': 0, '需求': 0, '偏好': 0, '未分类': 0}
    for _, _, cat, _ in kept:
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        else:
            cat_counts['未分类'] += 1
    non_noise = []
    noise_count = 0
    for ts, txt, cat, status in kept:
        if is_noise(txt) and cat is None:
            noise_count += 1
        else:
            non_noise.append((ts, txt, cat, status))

    # 需求状态统计
    req_status_counts = {'✅已解决': 0, '❌已取消': 0, '⏳待处理': 0}
    for _, _, cat, status in kept:
        if cat == '需求' and status:
            req_status_counts[status] = req_status_counts.get(status, 0) + 1

    lines = ['# 会话用户输入提取',
             f'（扫描 {len(files)} 个 jsonl，去重后 {len(kept)} 条真实用户消息{window_desc}，含 /compact 前部分）\n',
             '## 分类概览',
             f'- 需求 {cat_counts["需求"]} · 纠正 {cat_counts["纠正"]} · 踩坑 {cat_counts["踩坑"]} · 偏好 {cat_counts["偏好"]} · 未分类 {cat_counts["未分类"]} · 噪声折叠 {noise_count}\n']
    if req_status_counts['✅已解决'] + req_status_counts['❌已取消'] + req_status_counts['⏳待处理'] > 0:
        lines.append('')
        lines.append('## 需求状态概览')
        lines.append(f'- ✅已解决 {req_status_counts["✅已解决"]} · ❌已取消 {req_status_counts["❌已取消"]} · ⏳待处理 {req_status_counts["⏳待处理"]}')
    if not args.no_ledger:
        lines.append('')
        lines.append('## 跨会话未闭环需求（ledger，即「被顶掉」候选）')
        if carry:
            lines.append(f'- ⚠️ {len(carry)} 条需求在更早的会话提出后一直未闭环：')
            for it in carry[:15]:
                first = (it.get('first_seen') or '')[:10]
                nsess = len(it.get('sessions') or [])
                text = re.sub(r'\s+', ' ', it.get('text', ''))[:90]
                lines.append(f'  - ⏳ 首次 {first} · 跨 {nsess} 个会话 · {text}')
            if len(carry) > 15:
                lines.append(f'  - ... 另有 {len(carry) - 15} 条')
            lines.append('- 处置：逐条判 ✅/📋/❌ 三态之一后写回；不许静默放过（用户 CLAUDE.md 需求闭环铁律）')
        else:
            lines.append('- 无：本次会话的需求没有更早会话遗留的未闭环项')
        if ledger_path:
            lines.append(f'- ledger: {ledger_path}')
    for f in files:
        lines.append(f'- 源文件: {os.path.basename(f)}')
    lines.append('')

    # 已解决/已取消的需求默认折叠——回顾审计真正需要看的是 ⏳待处理 和非需求类消息。
    # 会话内检测标为终态的需求只在「需求状态概览」段显示数字，不逐条列全文（减噪音）。
    resolved_count = sum(1 for _, _, cat, status in non_noise
                         if cat == '需求' and status in _TERMINAL_STATUS)
    if args.show_resolved:
        show_msgs = non_noise
    else:
        show_msgs = [(ts, txt, cat, status) for ts, txt, cat, status in non_noise
                     if not (cat == '需求' and status in _TERMINAL_STATUS)]

    for ts, txt, cat, status in show_msgs:
        tag_parts = [cat] if cat else []
        if status:
            tag_parts.append(status)
        tag = f'（{" ".join(tag_parts)}）'
        lines.append(f'## [{ts}] {tag}')
        lines.append('')
        lines.append(txt)
        lines.append('')

    if resolved_count and not args.show_resolved:
        lines.append(f'## 已折叠 {resolved_count} 条已解决/已取消需求')
        lines.append('（只在上方概览显示数字，不逐条列全文。用 `--show-resolved` 恢复完整输出）')
        lines.append('')

    output = '\n'.join(lines)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(output)
        sys.stderr.write(f'已写入 {len(kept)} 条用户消息到 {args.out}\n')
    else:
        sys.stdout.write(output)

    # 写缓存（非 --no-cache 时，使下次短时间内的运行命中缓存）
    if not args.no_cache:
        write_cache(cache_meta_path, cache_output_path, args, files, output)


if __name__ == '__main__':
    main()
