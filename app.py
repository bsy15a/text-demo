"""
真迹职痕 — AI 灵活就业导航助手
================================
智联招聘「AI+求职」创新大赛参赛作品

核心洞察：
    超过60%的大学生最终从事了与专业不完全对口的工作，
    但市面上所有求职工具都假设用户"知道自己要找什么工作"。
    本产品服务于那些"不知道自己有什么、能去哪"的迷茫大学生。

三阶段闭环：
    阶段1 发现自我 → 阶段2 规划路径 → 阶段3 自信面试
"""

import streamlit as st
import requests

# ╔══════════════════════════════════════════════════════════════╗
# ║                    PAGE CONFIG & CSS                         ║
# ╚══════════════════════════════════════════════════════════════╝

st.set_page_config(
    page_title="真迹职痕 | AI灵活就业导航",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background: #fafbfc;
    }

    /* 卡片 */
    .card {
        background: white;
        border-radius: 6px;
        padding: 24px 28px;
        margin: 10px 0;
        border: 1px solid #e0e3e7;
    }

    /* 等待动画 */
    @keyframes gentleRise {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes softGlow {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.8; }
    }
    .wait-container {
        text-align: center;
        padding: 60px 20px;
    }
    .wait-message {
        animation: gentleRise 2s ease-out;
        color: #555;
        font-size: 1rem;
        line-height: 2;
    }
    .wait-dot {
        display: inline-block;
        width: 5px; height: 5px;
        border-radius: 50%;
        background: #aaa;
        margin: 0 3px;
        animation: softGlow 1.4s ease-in-out infinite;
    }
    .wait-dot:nth-child(2) { animation-delay: 0.3s; }
    .wait-dot:nth-child(3) { animation-delay: 0.6s; }
</style>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║                 SESSION STATE INIT                          ║
# ╚══════════════════════════════════════════════════════════════╝

DEFAULTS = {
    "phase": 1,
    "api_key": "",
    # 阶段1 数据
    "exp_q1": "",
    "exp_q1_name": "",
    "exp_q1_detail": "",
    "exp_q2": "",
    "exp_q3": "",
    "exp_q4": "",
    # 情景题：改为多选列表 + 自定义补充
    "pref_q1": [],   # 工作节奏（多选）
    "pref_q2": [],   # 成就感来源（多选）
    "pref_q3": [],   # 团队角色（多选）
    "pref_q4": [],   # 不确定性态度（多选）
    "pref_custom": "",  # 自定义补充
    "major": "",
    "grade": "大三",
    "career_paths": None,
    "abilities_raw": None,
    # 阶段2 数据
    "selected_path_idx": 0,
    "learning_plan": None,
    # 阶段3 数据
    "terminology": None,
    "interview_questions": None,
    "mock_answer": "",
    "mock_feedback": None,
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ╔══════════════════════════════════════════════════════════════╗
# ║                    API HELPER                               ║
# ╚══════════════════════════════════════════════════════════════╝

def call_qwen(prompt: str, system_prompt: str = "") -> str:
    """调用 AI API，支持多模型切换。"""
    api_key = st.session_state.api_key.strip()
    if not api_key:
        return "请先在左侧边栏输入 API Key"

    model_raw = st.session_state.get("model", "qwen-plus（推荐，稳定）")

    if "deepseek" in model_raw:
        endpoint = "https://api.deepseek.com/v1/chat/completions"
        model_id = "deepseek-chat"
    elif "turbo" in model_raw:
        endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        model_id = "qwen-turbo"
    else:
        endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        model_id = "qwen-plus"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": 3000,
            },
            timeout=90,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"API 错误 (HTTP {resp.status_code}): {resp.text[:300]}"
    except requests.Timeout:
        return "请求超时，请重试"
    except Exception as e:
        return f"请求失败: {str(e)}"


def is_api_error(text: str | None) -> bool:
    """检查 AI 返回的文本是否为错误信息。"""
    if text is None:
        return True
    return text.startswith("API 错误") or text.startswith("请求超时") or text.startswith("请求失败") or text.startswith("请先")


# ╔══════════════════════════════════════════════════════════════╗
# ║                    SIDEBAR                                  ║
# ╚══════════════════════════════════════════════════════════════╝

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 4px 0;">
        <span style="font-size:42px;">🧭</span>
        <h2 style="margin:4px 0 0 0; color:#1a365d;">真迹职痕</h2>
        <p style="color:#718096; font-size:13px; margin:2px 0;">你不只是你学的那个专业</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### API 设置")
    api_key_input = st.text_input(
        "通义千问 / DeepSeek API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-...",
        help="支持 阿里云 DashScope 或 DeepSeek API Key",
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input

    model_choice = st.selectbox(
        "模型选择",
        ["qwen-plus（推荐，稳定）", "qwen-turbo（更快）", "deepseek-chat（速度快，中文好）"],
        index=0,
        help="换模型可以加快分析速度",
    )
    st.session_state.model = model_choice

    st.markdown("---")

    st.markdown("### 📍 当前进度")
    phase_names = {1: "① 发现自我", 2: "② 规划路径", 3: "③ 自信面试"}
    for p in [1, 2, 3]:
        if st.session_state.phase == p:
            st.markdown(f"**🟢 {phase_names[p]}** ← 当前")
        elif st.session_state.phase > p:
            st.markdown(f"✅ {phase_names[p]}")
        else:
            st.markdown(f"⚪ {phase_names[p]}")

    st.markdown("---")

    st.markdown("### 使用指南")
    st.markdown("""
    1. **聊聊你的经历** — 不用觉得"不够好"
    2. **回答情景题** — 多选，没标准答案
    3. **看看发现** — 你可能忽略的可能性
    4. **获取学习计划** — 可执行的 30 天路线
    5. **面试准备** — 跨专业也有底气
    """)

    st.markdown("---")
    st.caption("智联招聘 AI 创新大赛 · 2026")
    st.caption("真迹职痕 v1.1 | AI+求职赛道")


# ╔══════════════════════════════════════════════════════════════╗
# ║                    MAIN HEADER                              ║
# ╚══════════════════════════════════════════════════════════════╝

# 进度条
col_p1, col_l1, col_p2, col_l2, col_p3 = st.columns([0.6, 1.2, 0.6, 1.2, 0.6], gap="small")
for col, p in [(col_p1, 1), (col_p2, 2), (col_p3, 3)]:
    with col:
        if st.session_state.phase > p:
            st.markdown(
                f'<div style="width:34px;height:34px;border-radius:50%;background:#48bb78;'
                f'color:white;display:flex;align-items:center;justify-content:center;'
                f'font-weight:700;font-size:14px;margin:0 auto;">✓</div>',
                unsafe_allow_html=True,
            )
        elif st.session_state.phase == p:
            st.markdown(
                f'<div style="width:34px;height:34px;border-radius:50%;background:#1a365d;'
                f'color:white;display:flex;align-items:center;justify-content:center;'
                f'font-weight:700;font-size:14px;margin:0 auto;">{p}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="width:34px;height:34px;border-radius:50%;background:#e2e8f0;'
                f'color:#a0aec0;display:flex;align-items:center;justify-content:center;'
                f'font-weight:700;font-size:14px;margin:0 auto;">{p}</div>',
                unsafe_allow_html=True,
            )
for idx, col in enumerate([col_l1, col_l2]):
    phase_num = idx + 1
    with col:
        if st.session_state.phase > phase_num:
            color = "#48bb78"
        else:
            color = "#e2e8f0"
        st.markdown(
            f'<div style="height:3px;background:{color};border-radius:2px;margin-top:16px;"></div>',
            unsafe_allow_html=True,
        )

phase_labels = {
    1: "发现自我 — 讲讲你做过的事",
    2: "规划路径 — 从「可能」到「可行」",
    3: "自信面试 — 跨专业也有底气",
}
st.markdown(
    f'<p style="text-align:center;color:#4a5568;font-size:14px;margin:4px 0 20px 0;">'
    f'{phase_labels[st.session_state.phase]}</p>',
    unsafe_allow_html=True,
)

st.markdown("---")


# ╔══════════════════════════════════════════════════════════════╗
# ║               PHASE 1: DISCOVER (发现自我)                  ║
# ╚══════════════════════════════════════════════════════════════╝

if st.session_state.phase == 1:

    if st.session_state.career_paths is None:
        step = "collect"
    else:
        step = "reveal"

    # ────────────────────────────────────────────
    # STEP: 收集信息
    # ────────────────────────────────────────────
    if step == "collect":

        st.markdown("""
        <div class="card fade-in">
            <h3 style="margin-top:0;font-size:1.2em;">先聊聊你做过的事</h3>
            <p style="color:#666;">不用很厉害的经历。课程作业、社团干活、帮过朋友的忙，都算。
            很多能力你自己可能都没注意到。</p>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        with col_a:
            st.session_state.major = st.text_input(
                "🎓 你的专业",
                value=st.session_state.major,
                placeholder="例如：材料科学与工程、市场营销、英语...",
            )
            st.session_state.grade = st.selectbox(
                "📅 当前年级",
                ["大一", "大二", "大三", "大四", "研一", "研二", "研三", "已毕业"],
                index=["大一","大二","大三","大四","研一","研二","研三","已毕业"].index(st.session_state.grade)
                if st.session_state.grade in ["大一","大二","大三","大四","研一","研二","研三","已毕业"]
                else 2,
            )

            st.session_state.exp_q1_name = st.text_input(
                "📚 课程名称或作业类型？（一条就够）",
                value=st.session_state.get("exp_q1_name", ""),
                placeholder="比如：Python课设、市场营销课期末报告、数据结构大作业...",
            )
            st.session_state.exp_q1_detail = st.text_area(
                "└ 在这个作业/课程里，你具体做了什么？",
                value=st.session_state.get("exp_q1_detail", ""),
                placeholder="用自己的话描述你做的事，越具体越好。比如：用Python写了一个学生成绩管理系统，负责数据库设计和界面部分，最后做了一次10分钟的课堂演示...",
                height=90,
            )
            st.session_state.exp_q1 = f"课程：{st.session_state.exp_q1_name}；具体内容：{st.session_state.exp_q1_detail}" if st.session_state.exp_q1_name or st.session_state.exp_q1_detail else ""

            st.session_state.exp_q2 = st.text_area(
                "🎪 参加过什么社团或活动？在里面干过什么具体的事？",
                value=st.session_state.exp_q2,
                placeholder="比如：在学生会做了半年的公众号排版、组织过一次班级春游、帮社团拉过赞助...",
                height=100,
            )

        with col_b:
            st.session_state.exp_q3 = st.text_area(
                "🤝 朋友一般因为什么事来找你帮忙？",
                value=st.session_state.exp_q3,
                placeholder="比如：PPT 做得好大家让你帮忙改、电脑出问题找你修、心情不好的时候找你聊天、选课的时候问你建议...\n\n这个问题的答案特别能反映你的隐性优势。",
                height=100,
            )

            st.session_state.exp_q4 = st.text_area(
                "💻 你用过的软件/工具/平台有哪些？（不需要精通，接触过就算）",
                value=st.session_state.exp_q4,
                placeholder="比如：用 Excel 填过表格、用 Canva 做过海报、剪映剪过视频、在 B站/GitHub/知乎 看过教程、用过 ChatGPT...\n\n不需要掌握，接触过、打开过、看过教程都算。这能帮 AI 理解你接触过的工具生态。",
                height=100,
            )

        # ── 偏好探测（改为多选 + 自定义） ──
        st.markdown("---")
        st.markdown("""
        <div class="card fade-in">
            <h3 style="margin-top:0;font-size:1.1em;">情景选择题 - 多选，选你觉得像的就行</h3>
            <p style="color:#666;">
                没有标准答案。如果都不像，选「以上都不太符合」然后用自己的话补充。
            </p>
        </div>
        """, unsafe_allow_html=True)

        pq1, pq2 = st.columns(2)
        pq3, pq4 = st.columns(2)

        NOT_FIT = "🤷 以上都不太符合我"

        with pq1:
            st.multiselect(
                "Q1. 哪种工作状态让你比较有满足感？（可多选）",
                options=[
                    "🔬 深入研究一个问题，把它彻底搞懂的时候",
                    "🤝 带着几个人一起把一件事做成的时候",
                    "📋 把一个混乱的东西整理得井井有条的时候",
                    "💡 冒出一个新点子然后立刻动手试的时候",
                    NOT_FIT,
                ],
                key="pref_q1",
            )
            if NOT_FIT in (st.session_state.pref_q1 or []):
                st.text_area(
                    "Q1 补充：你觉得哪种工作状态更符合你？",
                    placeholder="用自己的话描述就好...",
                    height=60,
                    key="pref_q1_custom",
                )
            else:
                st.session_state.pref_q1_custom = ""

        with pq2:
            st.multiselect(
                "Q2. 过去经历中，哪种时刻让你最有成就感？（可多选）",
                options=[
                    "🏆 解决了一个别人搞不定的难题",
                    "❤️ 帮助别人解决了他们的实际困难",
                    "🎨 做出一个看得见摸得着的成果/作品",
                    "🧩 发现了一种更聪明的方法来做某件事",
                    NOT_FIT,
                ],
                key="pref_q2",
            )
            if NOT_FIT in (st.session_state.pref_q2 or []):
                st.text_area(
                    "Q2 补充：哪种时刻让你最有成就感？",
                    placeholder="用自己的话描述就好...",
                    height=60,
                    key="pref_q2_custom",
                )
            else:
                st.session_state.pref_q2_custom = ""

        with pq3:
            st.multiselect(
                "Q3. 在团队/小组中，你通常更接近什么状态？（可多选）",
                options=[
                    "🔍 自己独立钻研，然后拿出成果",
                    "📢 协调大家，确保方向一致",
                    "✅ 认真执行分配到的任务",
                    "🌱 提出新方向，推动尝试不同做法",
                    NOT_FIT,
                ],
                key="pref_q3",
            )
            if NOT_FIT in (st.session_state.pref_q3 or []):
                st.text_area(
                    "Q3 补充：你在团队中通常是什么状态？",
                    placeholder="用自己的话描述就好...",
                    height=60,
                    key="pref_q3_custom",
                )
            else:
                st.session_state.pref_q3_custom = ""

        with pq4:
            st.text_area(
                "Q4. 还有什么想补充的吗？（选填）",
                placeholder="比如你特别在意的工作环境、你不想做的事、或者任何觉得 AI 应该知道的事...",
                height=120,
                key="pref_custom",
            )

        # ── 提交按钮 ──
        st.markdown("---")
        has_prefs = any([
            st.session_state.pref_q1,
            st.session_state.pref_q2,
            st.session_state.pref_q3,
            st.session_state.get("pref_custom", "").strip(),
            st.session_state.get("pref_q1_custom", "").strip(),
            st.session_state.get("pref_q2_custom", "").strip(),
            st.session_state.get("pref_q3_custom", "").strip(),
        ])
        can_submit = all([
            st.session_state.major.strip(),
            (st.session_state.get("exp_q1_name","").strip() and st.session_state.get("exp_q1_detail","").strip()) or st.session_state.exp_q2.strip() or st.session_state.exp_q3.strip(),
            has_prefs,
        ])

        submit_col, _ = st.columns([1, 3])
        with submit_col:
            if st.button("开始分析", type="primary", disabled=not can_submit, use_container_width=True):
                if not can_submit:
                    st.warning("请至少填写专业、一段经历，并至少选择或补充一个偏好描述")
                else:
                    # ── 用 st.status 分步显示进度（解决等待焦虑） ──
                    with st.status("正在分析...", expanded=True) as analysis_status:

                        import random
                        healing_messages = [
                            "每个人走过的路都算数，即使当时觉得平平无奇",
                            "很多能力就像呼吸，你一直在用，却从未注意过它",
                            "你做过的每一件小事，都在悄悄塑造你",
                            "不用担心\"不够好\"，重要的是你做了什么",
                            "有时候别人看到你的闪光点，比你自己更清楚",
                            "慢慢来，好的发现值得等待",
                            "每段经历都是拼图的一块，现在我们来拼起来看看",
                        ]
                        msg = random.choice(healing_messages)

                        st.markdown(f"""
                        <div class="wait-container">
                            <div class="wait-message">{msg}</div>
                            <div style="margin-top:16px;">
                                <span class="wait-dot"></span>
                                <span class="wait-dot"></span>
                                <span class="wait-dot"></span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Step 1: 隐性能力提取
                        ability_prompt = f"""你是一位资深职业规划顾问，擅长从普通大学生的日常经历中提取隐性可迁移能力。

请分析这位学生的经历，提取出 TA 可能自己都没意识到的能力。

---
【学生背景】
- 专业：{st.session_state.major}
- 年级：{st.session_state.grade}

【TA 的经历自述】
1. 课程设计/大作业：{st.session_state.exp_q1 or '（未填写）'}
2. 社团/活动经历：{st.session_state.exp_q2 or '（未填写）'}
3. 朋友常找 TA 帮忙的事：{st.session_state.exp_q3 or '（未填写）'}
4. 接触过/使用过的软件工具：{st.session_state.exp_q4 or '（未填写）'}

【TA 的偏好选择（多选）】
- 工作状态偏好：{', '.join(st.session_state.pref_q1) if st.session_state.pref_q1 else '（未选择）'}{(' / 补充：' + st.session_state.get('pref_q1_custom','')) if st.session_state.get('pref_q1_custom','').strip() else ''}
- 成就感来源：{', '.join(st.session_state.pref_q2) if st.session_state.pref_q2 else '（未选择）'}{(' / 补充：' + st.session_state.get('pref_q2_custom','')) if st.session_state.get('pref_q2_custom','').strip() else ''}
- 团队角色：{', '.join(st.session_state.pref_q3) if st.session_state.pref_q3 else '（未选择）'}{(' / 补充：' + st.session_state.get('pref_q3_custom','')) if st.session_state.get('pref_q3_custom','').strip() else ''}
- 补充说明：{st.session_state.get('pref_custom','') or '（未填写）'}
---

请你从以上信息中做"隐性能力提取"。重要规则：

1. **关于软件/工具**：如果学生提到用过某些软件，不要把"用过"直接等同于"精通"。你应当理解为"TA 至少接触过这类工具的思维方式"和"TA 有主动探索的意愿"。例如"用过 Canva"可以映射为「有基础的视觉表达意识」而不是「会设计」。

2. **严禁自行配对经历**：每项能力只能来自用户原文中有明确语境的描述。不得把来自不同问题的经历拼凑成一项能力。规则如下：
   - 每项能力必须标注来源是哪道题（如"来自经历1"），且只能有一个来源
   - 用户在"课程作业"里提到写了代码，在"社团经历"里提到做了演讲，绝对不能合并为"项目汇报能力"或"边写代码边演讲"——这是两件独立的事
   - 只有用户在同一段描述中明确写出了两件事的关联（如"在课程汇报中展示了我写的代码"），才可以提取跨维度能力
   - 如果无法确定某项能力的单一来源，宁可不提取，也不要猜测关联

3. 从每段经历中提取 2-3 项可迁移能力（要具体，不要只说"沟通能力"——要说"向非技术受众解释复杂信息的表达能力"这类可验证的描述）

4. 将每项能力和 TA 的具体经历关联起来（"因为你提到..."）

5. 汇总 TA 的能力画像：3-5 个核心可迁移能力维度

6. 根据偏好选择，推断 TA 可能适合的工作类型（不是具体岗位，是工作性质）

请用务实、平静的语气。不要用感叹号。不要过度抬高——你是在分析，不是在推销。直接说发现。如果某些推断把握不大，请标注'可能'。"""

                        abilities = call_qwen(
                            ability_prompt,
                            system_prompt="你是一位务实、克制的职业规划师。说话风格：具体、有据、不煽情。不使用'惊人''卓越''一定会'等过度肯定词汇。不把'用过软件'等同于'熟练掌握'。每次输出都引用用户原文作为证据，不确定的地方就说'可能'。",
                        )
                        st.session_state.abilities_raw = abilities

                        # Step 2 提示
                        msg2 = random.choice([
                            "你的能力可能适合一些你从未想过的方向",
                            "换个角度看自己，会发现新的可能性",
                            "有时候合适的工作，不在你原本的视野里",
                            "跨出专业的第一步，其实你已经准备好了",
                        ])
                        st.markdown(f"""
                        <div class="wait-container">
                            <div class="wait-message">{msg2}</div>
                            <div style="margin-top:16px;">
                                <span class="wait-dot"></span>
                                <span class="wait-dot"></span>
                                <span class="wait-dot"></span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Step 2: 跨界路径生成
                        path_prompt = f"""你是一位精通跨行业人才流动的职业规划专家。

基于以下分析，请你为这位学生推荐 3 条职业路径。

---
【隐性能力分析结果】
{abilities}

【学生基本信息】
- 专业：{st.session_state.major}
- 年级：{st.session_state.grade}
---

## 重要约束：
1. **路径一和路径二必须是跨界方向**——不是该专业的传统对口岗位，要有真正的跨界感，覆盖不同类型（如一个偏技术、一个偏业务或创意），这是推荐的核心和重点
2. **路径三是对口锚点**——列举 2-3 个符合该学生能力写照的本专业对口岗位方向，简要说明匹配理由即可，不需要展开30天计划，作为参照而非重点
3. 每条路径必须有技能迁移的明确逻辑（学生的哪些能力可以迁移过去）
4. **跨界路径必须有真正的跨界感**：不能只是"本专业技能应用到另一个行业"（如计算机专业推荐"医疗AI工程师"本质还是在做程序员，不算跨界）。真正的跨界是能力迁移到不同的工作性质，如从理工科背景迁移到产品、运营、内容、咨询等方向
5. 路径必须是真实存在的岗位，不是凭空编造的
6. 优先推荐需求量大、增长中的新兴交叉领域

## 请严格按照以下格式输出：

### 🛤️ 路径一：[跨界岗位名称]
- **技能重合度**：[估计百分比，如 65%]
- **为什么你能做**：[用学生的真实经历和能力来说服 TA —— 3-4 句话]
- **就差这一点**：[列出 2-3 个关键技能缺口，每个用一句话说明]
- **市场参考**：[薪资范围 + 需求趋势，一句话]
- **一个 30 天微项目**：[具体可做的验证项目，产出能写到简历上 —— 2-3 句话]

### 🛤️ 路径二：[跨界岗位名称]
（同路径一格式）

### 🔖 路径三（对口参考）：[本专业方向]
- **匹配说明**：[结合学生真实经历，说明为什么这些对口方向也适合 TA —— 2-3 句话]
- **代表岗位**：[列举 2-3 个具体岗位名称]
- **说明**：以上为专业对口方向，仅供参考。如果还在迷茫，可以试着接触路径一和路径二的跨界方向。

## 语气和内容约束：
- 不要使用"惊人""卓越""绝对""一定可以""包你满意"等过度肯定或推销性词汇
- 薪资数据标注"参考范围"，不要写虚高数字。如果不确定就说"建议查招聘平台获取最新数据"
- "为什么你能做"部分必须引用学生原文中的具体细节，不许凭空编造能力
- 如果某项推断把握不大，标注"可能"或"或许"
- 不要用感叹号，保持平静务实的语气"""

                        paths = call_qwen(path_prompt)
                        st.session_state.career_paths = paths

                        # 完成
                        analysis_status.update(
                            label="✅ 分析完成！AI 从你的经历中发掘出了你可能从未想过的可能性",
                            state="complete",
                        )

                    st.rerun()

    # ────────────────────────────────────────────
    # STEP: 展示结果
    # ────────────────────────────────────────────
    elif step == "reveal":

        if not is_api_error(st.session_state.abilities_raw):
            with st.expander("🔬 查看 AI 如何分析你的隐性能力", expanded=False):
                st.markdown(st.session_state.abilities_raw)

        st.markdown("""
        <div style="text-align:center; padding:20px 0 10px 0;" class="fade-in">
            <h2 style="color:#1a365d;">基于你的经历，看看这些方向</h2>
            <p style="color:#718096;">前两条是跨界探索，第三条是本专业参考</p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.career_paths:
            st.markdown(st.session_state.career_paths)
        else:
            st.warning("路径生成失败，请返回上一步重试")

        st.markdown("---")

        col_act1, col_act2, col_act3 = st.columns([1, 1, 2])
        with col_act1:
            if st.button("🔄 重新分析", use_container_width=True):
                st.session_state.career_paths = None
                st.session_state.abilities_raw = None
                st.rerun()
        with col_act2:
            paths_ready = not is_api_error(st.session_state.career_paths)
            if st.button("👉 进入阶段2：规划学习路径", type="primary", use_container_width=True,
                         disabled=not paths_ready):
                st.session_state.phase = 2
                st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║               PHASE 2: NAVIGATE (规划路径)                  ║
# ╚══════════════════════════════════════════════════════════════╝

if st.session_state.phase == 2:

    st.markdown("""
    <div class="card fade-in">
        <h3 style="margin-top:0;">🗺️ 选择你想深入探索的路径</h3>
        <p style="color:#718096;">从阶段 1 发现的三条路径中选一条，AI 将为你生成专属学习计划。</p>
    </div>
    """, unsafe_allow_html=True)

    path_choice = st.radio(
        "选择一条路径：",
        ["路径一", "路径二", "路径三"],
        index=st.session_state.selected_path_idx,
        horizontal=True,
        key="path_selector",
    )
    st.session_state.selected_path_idx = {"路径一": 0, "路径二": 1, "路径三": 2}[path_choice]

    if st.session_state.career_paths:
        with st.expander("📋 回顾阶段 1 发现的路径（点击展开）", expanded=False):
            st.markdown(st.session_state.career_paths)

    st.markdown("---")
    gen_col, _ = st.columns([1, 3])
    with gen_col:
        if st.button("🚀 为这条路径生成 30 天学习计划", type="primary", use_container_width=True):
            with st.status("🧠 AI 正在定制学习路径...", expanded=True) as plan_status:

                st.markdown("""
                <div class="thinking-indicator">
                    <span class="thinking-dot"></span>
                    <span class="thinking-dot"></span>
                    <span class="thinking-dot"></span>
                    <span style="margin-left:10px;color:#718096;">分析技能差距 + 设计四周学习计划 + 匹配学习资源...</span>
                </div>
                """, unsafe_allow_html=True)

                plan_prompt = f"""你是一位实战派职业导师，擅长为跨专业求职者设计"刚好够用"的学习路径。

---
【学生背景】
- 专业：{st.session_state.major}
- 年级：{st.session_state.grade}

【阶段1 发现的 3 条路径（完整）】
{st.session_state.career_paths}

【用户选择了】
{path_choice}
---

请你为这条路径生成一个**真实可执行的 30 天学习计划**。

## 核心理念：
- 不是让用户"成为专家"，而是让用户"刚好够拿到面试机会"
- 聚焦最小必要技能（Minimum Viable Skills），不要堆砌
- 每周有具体的产出物（可以写到简历上的那种）
- **重要**：考虑到大部分大学生习惯了被动学习（听课、跟着教程做），你需要推荐具体的、有名字的资源，而不是泛泛说"去学XX"。大学生最习惯的学习渠道是 B站、知乎、GitHub。

## 请严格按照以下格式输出：

### 📊 技能差距一览
用文字列出：当前已有能力 vs 目标岗位需要但你还缺的能力，逐项对比。

### 🗓️ 四周学习计划

**第 1 周：基础认知建立**
- 学习任务（具体到可执行的行动，比如"看XX的视频第1-3集"而不是"学习XX概念"）：
- 📺 推荐资源（给出搜索关键词或真实资源；如果无法确认真实性，只写搜索建议）：
- 本周产出物：
- 预计耗时：（考虑大学生实际每周可投入 10-15 小时）

**第 2 周：核心技能上手**
- 学习任务：
- 📺 推荐资源（搜索关键词或真实资源；无法确认真实性就只写搜索建议）：
- 本周产出物：
- 预计耗时：

**第 3 周：实战练手**
- 学习任务：
- 📺 推荐资源（搜索关键词或真实资源；无法确认真实性就只写搜索建议）：
- 本周产出物：
- 预计耗时：

**第 4 周：成果包装**
- 学习任务：
- 📺 推荐资源（搜索关键词或真实资源；无法确认真实性就只写搜索建议）：
- 本周产出物：
- 预计耗时：

### 🔨 验证性微项目（30 天可完成）
- **项目名称**：
- **项目描述**：（2-3 句话，说清楚要做什么）
- **技术栈/工具**：
- **产出物**：（能写到简历上的具体成果，如一个 GitHub 仓库、一份分析报告、一个作品集页面等）
- **简历可写法**：（给一句可以直接用在简历上的描述）

### 📚 学习资源建议
至少推荐 3 个学习方向，每个都要有：
- **搜索关键词 + 平台**（如"在B站搜索Python入门"或"知乎搜数据分析实战"）
- **为什么学这个方向**（1 句话）
- **怎么用**（重点看什么内容/做完什么练习）
- 如果能确认某个资源真实存在可以写名字，但不确定时只写搜索方式

请注意：
- 学习任务面向的是习惯被动学习的大学生，要像课程表一样具体——告诉 TA"这周看哪几个视频、做完哪个练习"
- 产出物必须是可以展示的，不能是"理解了某个概念"
- 考虑大学生的实际时间和精力（每周 10-15 小时）
- **严禁编造资源**：你不能确认某个UP主或课程真实存在时，绝对不要写具体名称。写成「B站搜索"XXX"」或「知乎搜XXX话题下的高赞回答」这种搜索建议形式。这是硬性要求——编造一个不存在的UP主或课程，比不推荐更糟糕。如果你完全不确定有什么资源，就在整栏写「建议在B站/知乎搜索以下关键词自行筛选：XXX」"""

                plan = call_qwen(plan_prompt)
                st.session_state.learning_plan = plan

                plan_status.update(label="✅ 学习计划已生成！", state="complete")

            st.rerun()

    if st.session_state.learning_plan:
        st.markdown("---")
        if not is_api_error(st.session_state.learning_plan):
            st.markdown(st.session_state.learning_plan)

            st.markdown("---")
            col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
            with col_b1:
                if st.button("⬅ 返回阶段 1", use_container_width=True):
                    st.session_state.phase = 1
                    st.rerun()
            with col_b2:
                if st.button("👉 进入阶段3：面试准备", type="primary", use_container_width=True):
                    st.session_state.phase = 3
                    st.rerun()
        else:
            st.error(st.session_state.learning_plan)
            if st.button("🔄 重试"):
                st.session_state.learning_plan = None
                st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║            PHASE 3: INTERVIEW (自信面试)                    ║
# ╚══════════════════════════════════════════════════════════════╝

if st.session_state.phase == 3:

    st.markdown("""
    <div class="card fade-in">
        <h3 style="margin-top:0;">🎤 跨专业面试，你的不一样反而是优势</h3>
        <p style="color:#718096;">
            面试官最怕的不是"你不懂某个术语"，而是"你因为害怕而不自信"。
            下面三个模块帮你武装到位。
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_term, tab_questions, tab_mock = st.tabs([
        "📖 术语降维翻译",
        "❓ 面试高频问题",
        "🎯 深度模拟",
    ])

    path_idx = st.session_state.selected_path_idx
    path_label = ["路径一", "路径二", "路径三"][path_idx]

    # ── Tab 1: 术语降维 ──
    with tab_term:
        st.markdown("#### 这个岗位的核心术语，用你听得懂的方式解释")

        if st.button("🔬 生成术语降维翻译", key="btn_term", type="primary"):
            term_prompt = f"""你是一位善于用类比解释复杂概念的技术写作者。

---
【学生背景】
- 专业：{st.session_state.major}
- 年级：{st.session_state.grade}

【学生选择探索的路径】
{path_label}（以下为该路径的完整描述）

{st.session_state.career_paths}

【学生隐性能力分析】
{st.session_state.abilities_raw or '（未提供）'}
---

请为该目标岗位生成一份"术语降维翻译表"。

## 要求：
1. 列出该岗位面试中最可能出现的 **10 个核心行业术语**
2. 每个术语给出：
   - **通俗解释**（1 句话，让非科班的人也能懂）
   - **类比理解**（用该学生的专业 "{st.session_state.major}" 中可能熟悉的概念做类比——如果学生的专业和该岗位毫无关联，就用日常生活类比）
   - **面试中怎么说**（一句示范，教学生如何在面试中自然地提及这个术语，显示"我做过功课"但不装专家）

## 格式：
| 术语 | 通俗解释 | 用你的背景理解 | 面试中这样说 |
|------|---------|---------------|-------------|
| ... | ... | ... | ... |

另外，在表格前用 2-3 句话告诉学生：面试官并不期待跨专业的人精通所有术语，他们看的是学习态度和迁移能力。"""

            with st.spinner("🤔 AI 正在做术语类比翻译..."):
                terminology = call_qwen(term_prompt)
                st.session_state.terminology = terminology
            st.rerun()

        if st.session_state.terminology:
            if not is_api_error(st.session_state.terminology):
                st.markdown(st.session_state.terminology)
            else:
                st.error(st.session_state.terminology)

    # ── Tab 2: 面试高频问题（增强项目针对性） ──
    with tab_questions:
        st.markdown("#### 针对你的情况和目标岗位，最可能被问的问题")

        if st.button("❓ 生成高频问题 + 回答框架", key="btn_questions", type="primary"):
            q_prompt = f"""你是一位经验丰富的面试官，面试过大量跨专业求职者。

---
【学生背景】
- 专业：{st.session_state.major}
- 年级：{st.session_state.grade}
- 已有经历：{st.session_state.exp_q1}；{st.session_state.exp_q2}；{st.session_state.exp_q3}

【目标路径】
{path_label}：
{st.session_state.career_paths}
---

请生成**6-7 个该岗位面试中，针对这位跨专业候选人最可能被问到的问题**。

## 重要：问题分配
- **3-4 个问题必须围绕学生的项目/经历展开**（这是面试重头戏！面试官70%的时间在追问项目细节）
  - 例如："你做过XX项目，当时为什么选择这个技术方案？"
  - "你在项目中遇到的最大困难是什么？怎么解决的？"
  - "如果让你重新做这个项目，你会怎么改进？"
  - 请根据学生真实的经历（哪怕是课程作业）来设计追问
- **1 个跨专业必问题**："你是学{st.session_state.major}的，为什么想来做这个？"
- **1 个行业认知题**："你对这个行业了解多少？最近关注了什么动态？"
- **1 个行为面试题**：描述一个能体现学生可迁移能力的场景

对每个问题，请用以下格式：

### Q1：[问题原文]
- **面试官为什么问这个**（他们真正想考察什么）：
- **你的回答框架**（不是直接给答案，而是给结构：先说什么→再说什么→最后说什么）：
- **你可以用的素材**（结合学生真实经历中的具体细节来支撑回答——如果学生没有相关项目经历，就建议 TA 如何把课程作业/社团经历包装成项目经验来回答）：
- **避坑提醒**（跨专业考生在这个问题上的常见错误）：

（Q2-Q7 同样格式）

语气要像一位严厉但真心为学生好的导师——指出问题但不打击信心。"""

            with st.spinner("🤔 AI 正在分析面试考察重点..."):
                questions = call_qwen(q_prompt)
                st.session_state.interview_questions = questions
            st.rerun()

        if st.session_state.interview_questions:
            if not is_api_error(st.session_state.interview_questions):
                st.markdown(st.session_state.interview_questions)
            else:
                st.error(st.session_state.interview_questions)

    # ── Tab 3: 深度模拟 ──
    with tab_mock:
        st.markdown("#### 选一个问题，写出你的回答 — AI 逐段点评")

        if st.session_state.interview_questions:
            st.markdown("**📝 你的回答：**")
            mock_answer = st.text_area(
                "写下你对面试官的回答（也可以是语音转文字贴过来）",
                value=st.session_state.mock_answer,
                placeholder="面试官问完问题后，你会怎么回答？不需要完美，把你想说的写下来就好...",
                height=180,
                key="mock_answer_input",
            )
            st.session_state.mock_answer = mock_answer

            if st.button("🎯 AI 点评我的回答", type="primary", disabled=not mock_answer.strip()):
                feedback_prompt = f"""你是一位温和但直率的面试教练。你的目标是帮助学生改进，而不是打击他们。

---
【学生背景】
- 专业：{st.session_state.major}
- 目标路径：{path_label}

【面试问题和回答框架】
{st.session_state.interview_questions}

【学生的回答】
{mock_answer}
---

请对学生的回答进行点评和改进建议：

## 格式：

### ✅ 做得好的地方（至少 2 点）
具体指出哪里好，不要空泛说"很好"。

### 🔧 可以改进的地方（最多 3 点）
每条指出具体问题 + 为什么是问题 + 怎么改。

### 📝 优化版回答示范
不是让学生背诵，而是给一个参考——你可以这样说（150-200 字）。

### 💡 一个"把跨专业变优势"的技巧
教学生在回答中如何自然地把自己本专业的独特视角转化为加分项，而不是道歉。

## 语气要求：
- 先肯定，再提建议
- 批评要具体，不给空话
- 让学生感到"我可以做到"，而不是"我差太远了"
- 不要说"作为 AI"之类的套话"""

                with st.spinner("🤔 AI 正在分析你的回答..."):
                    feedback = call_qwen(feedback_prompt)
                    st.session_state.mock_feedback = feedback
                st.rerun()

            if st.session_state.mock_feedback:
                st.markdown("---")
                if not is_api_error(st.session_state.mock_feedback):
                    st.markdown(st.session_state.mock_feedback)
                else:
                    st.error(st.session_state.mock_feedback)
        else:
            st.info("👆 请先在「面试高频问题」标签页生成问题，再来这里练习回答")

    st.markdown("---")
    col_c1, col_c2, col_c3 = st.columns([1, 1, 2])
    with col_c1:
        if st.button("⬅ 返回阶段 2", use_container_width=True):
            st.session_state.phase = 2
            st.rerun()
    with col_c2:
        if st.button("🔄 回到起点重新开始", use_container_width=True):
            for key in DEFAULTS:
                st.session_state[key] = DEFAULTS[key]
            st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║                    FOOTER                                   ║
# ╚══════════════════════════════════════════════════════════════╝

st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:20px 0; color:#a0aec0; font-size:13px;">
    <p>🧭 <strong>真迹职痕</strong> v1.1 — 你不只是你学的那个专业</p>
    <p>智联招聘「AI+求职」创新大赛参赛作品 · 2026 | AI+求职赛道</p>
    <p style="font-size:11px; margin-top:8px;">
        本 Demo 使用 通义千问 (Qwen-Plus) 大模型提供 AI 能力 |
        所有分析结果由 AI 生成，仅供参考
    </p>
</div>
""", unsafe_allow_html=True)