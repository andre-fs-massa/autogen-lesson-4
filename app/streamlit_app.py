import streamlit as st

import streamlit as st
st.write("Key starts with:", st.secrets.get("OPENAI_API_KEY", "NOT FOUND")[:8])

from agents import (
    run_game,
    reset_game,
    get_board_svg,
    get_agent_interactions,
    get_board_proxy_history,
)


# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title=
    "AI Agent Playground — Chess",

    layout="wide"
)


# =====================================
# HEADER
# =====================================
st.title(
    "AI Agent Playground"
)

st.caption(
    "Conversational chess with multi-agent tool use using AutoGen and OpenAI"
)

st.divider()


# =====================================
# SIDEBAR
# =====================================
with st.sidebar:

    st.subheader(
        "Game Controls"
    )

    turns = st.slider(
        "Max turns",

        min_value=2,

        max_value=10,

        value=4,

        step=2,
    )

    start_button = (
        st.button(
            "Start New Game",
            use_container_width=
            True
        )
    )

    st.divider()

    st.markdown("""
### What this demonstrates

- Tool use  
- Multi-agent orchestration  
- Nested chats  
- Function calling  
- Stateful environment  
- AI-to-AI collaboration  
- Conversational gameplay  
""")


# =====================================
# MAIN LAYOUT
# =====================================
left, right = st.columns(
    [1.15, 1]
)


# =====================================
# START GAME
# =====================================
if start_button:

    reset_game()

    with st.spinner(
        "Agents are playing..."
    ):

        try:

            result = run_game(
                turns
            )

            st.session_state[
                "game_result"
            ] = result

        except Exception as e:

            st.error(
                str(e)
            )


# =====================================
# DISPLAY RESULTS
# =====================================
if (
    "game_result"
    in st.session_state
):

    result = (
        st.session_state[
            "game_result"
        ]
    )

    # =====================================
    # LEFT COLUMN
    # =====================================
    with left:

        st.subheader(
            "Chess Board"
        )

        board_svg = (
            get_board_svg()
        )

        # Responsive board
        st.markdown(
            """
            <style>
            .chess-board-container svg {
                width: 100% !important;
                height: auto !important;
                max-width: 460px !important;
                display: block;
                margin: auto;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="chess-board-container">
                {board_svg}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # =====================================
        # BOARD PROXY INTERACTIONS
        # =====================================
        st.subheader(
            "Board Proxy Interactions"
        )

        proxy_history = (
            get_board_proxy_history()
        )

        if proxy_history:

            for interaction in (
                proxy_history
            ):

                with st.expander(
                    (
                        f"{interaction['from']} "
                        f"→ "
                        f"{interaction['to']}"
                    ),
                    expanded=False
                ):

                    st.write(
                        interaction[
                            "message"
                        ]
                    )

        else:

            st.info(
                "No board interactions yet."
            )

    # =====================================
    # RIGHT COLUMN
    # =====================================
    with right:

        st.subheader(
            "Agent Conversation"
        )

        for msg in (
            result.chat_history
        ):

            role = msg.get(
                "name"
            )

            content = (
                msg.get(
                    "content",
                    ""
                )
            )

            # Skip empty/system messages
            if (
                role is None
                or not content
            ):
                continue

            with st.expander(
                role,
                expanded=False
            ):

                st.write(
                    content
                )

        st.divider()

        # =====================================
        # TOOL USAGE
        # =====================================
        st.subheader(
            "Tool Usage"
        )

        tool_calls = (
            get_agent_interactions()
        )

        if tool_calls:

            for tool in (
                tool_calls
            ):

                with st.expander(
                    tool["tool"],
                    expanded=False
                ):

                    st.write(
                        tool[
                            "content"
                        ]
                    )

        else:

            st.info(
                "No tool calls yet."
            )