import os

from pathlib import Path
from dotenv import load_dotenv

import chess
import chess.svg

from autogen import (
    ConversableAgent,
    register_function,
)


# =====================================
# LOAD ENVIRONMENT
# =====================================
import streamlit as st

# Load from Streamlit secrets if available, fallback to .env locally
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    openai_api_key = os.getenv("OPENAI_API_KEY")

llm_config = {
    "config_list": [
        {
            "model": "gpt-4o-mini",
            "api_key": openai_api_key,
        }
    ]
}


# =====================================
# MODEL CONFIG
# =====================================
llm_config = {
    "config_list": [
        {
            "model": "gpt-4o-mini",
            "api_key": os.getenv(
                "OPENAI_API_KEY"
            ),
        }
    ]
}


# =====================================
# GLOBAL STATE
# =====================================
board = chess.Board()

made_move = False

agent_interactions = []

board_proxy_history = []


# =====================================
# RESET GAME
# =====================================
def reset_game():

    global board
    global made_move
    global agent_interactions
    global board_proxy_history

    board = chess.Board()

    made_move = False

    agent_interactions = []

    board_proxy_history = []


# =====================================
# TOOL:
# GET LEGAL MOVES
# =====================================
def get_legal_moves():

    legal_moves = (
        ",".join(
            str(move)
            for move
            in board.legal_moves
        )
    )

    result = (
        "Possible moves are: "
        + legal_moves
    )

    agent_interactions.append(
        {
            "tool":
            "get_legal_moves()",

            "content":
            result,
        }
    )

    return result


# =====================================
# TOOL:
# MAKE MOVE
# =====================================
def make_move(
    move: str
):

    global made_move

    chess_move = (
        chess.Move
        .from_uci(move)
    )

    board.push_uci(
        str(chess_move)
    )

    made_move = True

    piece = (
        board.piece_at(
            chess_move.to_square
        )
    )

    piece_symbol = (
        piece.unicode_symbol()
    )

    piece_name = (
        chess.piece_name(
            piece.piece_type
        ).capitalize()
    )

    move_text = (
        f"{piece_name} "
        f"({piece_symbol}) "
        f"moved from "
        f"{chess.SQUARE_NAMES[chess_move.from_square]} "
        f"to "
        f"{chess.SQUARE_NAMES[chess_move.to_square]}"
    )

    agent_interactions.append(
        {
            "tool":
            "make_move()",

            "content":
            move_text,
        }
    )

    return move_text


# =====================================
# TERMINATION CHECK
# =====================================
def check_made_move(
    msg
):

    global made_move

    if made_move:

        made_move = False

        return True

    return False


# =====================================
# CREATE AGENTS
# =====================================
def create_agents():

    player_white = (
        ConversableAgent(
            name=
            "PlayerWhite",

            system_message=
            (
                "You are a chess player "
                "and you play as white. "
                "First call "
                "get_legal_moves() "
                "to get legal moves. "
                "Then call "
                "make_move(move) "
                "to make a move. "
                "After making a move, "
                "make fun chitchat."
            ),

            llm_config=
            llm_config,
        )
    )

    player_black = (
        ConversableAgent(
            name=
            "PlayerBlack",

            system_message=
            (
                "You are a chess player "
                "and you play as black. "
                "First call "
                "get_legal_moves() "
                "to get legal moves. "
                "Then call "
                "make_move(move) "
                "to make a move. "
                "After making a move, "
                "make fun chitchat."
            ),

            llm_config=
            llm_config,
        )
    )

    board_proxy = (
        ConversableAgent(
            name=
            "BoardProxy",

            llm_config=
            False,

            is_termination_msg=
            check_made_move,

            default_auto_reply=
            "Please make a move.",

            human_input_mode=
            "NEVER",
        )
    )

    # Register tools
    for caller in [
        player_white,
        player_black
    ]:

        register_function(
            get_legal_moves,
            caller=caller,
            executor=board_proxy,
            name="get_legal_moves",
            description=
            "Get legal moves."
        )

        register_function(
            make_move,
            caller=caller,
            executor=board_proxy,
            name="make_move",
            description=
            "Make a chess move."
        )

    # Nested chats
    player_white.register_nested_chats(
        trigger=
        player_black,

        chat_queue=[
            {
                "sender":
                board_proxy,

                "recipient":
                player_white,

                "summary_method":
                "last_msg",

                "silent":
                True,
            }
        ],
    )

    player_black.register_nested_chats(
        trigger=
        player_white,

        chat_queue=[
            {
                "sender":
                board_proxy,

                "recipient":
                player_black,

                "summary_method":
                "last_msg",

                "silent":
                True,
            }
        ],
    )

    return (
        player_white,
        player_black
    )


# =====================================
# RUN GAME
# =====================================
def run_game(
    turns=4
):

    (
        player_white,
        player_black
    ) = create_agents()

    result = (
        player_black
        .initiate_chat(
            player_white,

            message=
            "Let's play chess! "
            "Your move.",

            max_turns=
            turns,
        )
    )

    # Create proxy history
    for tool in agent_interactions:

        board_proxy_history.append(
            {
                "from":
                "BoardProxy",

                "to":
                (
                    "PlayerWhite"
                    if len(
                        board_proxy_history
                    ) % 2 == 0
                    else
                    "PlayerBlack"
                ),

                "message":
                tool["content"]
            }
        )

    return result


# =====================================
# BOARD SVG
# =====================================
def get_board_svg():

    return chess.svg.board(
        board=board,
        size=520
    )


# =====================================
# GETTERS
# =====================================
def get_agent_interactions():

    return agent_interactions


def get_board_proxy_history():

    return board_proxy_history