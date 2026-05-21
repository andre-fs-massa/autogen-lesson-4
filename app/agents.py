import os
from pathlib import Path

from dotenv import load_dotenv

import chess
import chess.svg

from autogen import (
    ConversableAgent,
)


# =====================================
# LOAD ENVIRONMENT
# =====================================
BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

load_dotenv(
    BASE_DIR / ".env"
)


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
# GAME STATE
# =====================================
board = chess.Board()

agent_interactions = []

board_proxy_history = []


# =====================================
# RESET GAME
# =====================================
def reset_game():

    global board
    global agent_interactions
    global board_proxy_history

    board = chess.Board()

    agent_interactions = []

    board_proxy_history = []


# =====================================
# TOOL:
# GET LEGAL MOVES
# =====================================
def get_legal_moves() -> str:

    legal_moves = ",".join(
        str(move)
        for move
        in board.legal_moves
    )

    result = (
        "Possible legal moves are: "
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

    board_proxy_history.append(
        {
            "from":
            "Player Agent",

            "to":
            "BoardProxy",

            "message":
            "Requested legal moves."
        }
    )

    return result


# =====================================
# TOOL:
# MAKE MOVE
# =====================================
def make_move(
    move: str
) -> str:

    try:

        chess_move = (
            chess.Move
            .from_uci(move)
        )

        if (
            chess_move
            not in board.legal_moves
        ):

            return (
                f"Illegal move: "
                f"{move}"
            )

        board.push(
            chess_move
        )

        piece = (
            board.piece_at(
                chess_move.to_square
            )
        )

        piece_symbol = (
            piece.unicode_symbol()
            if piece
            else ""
        )

        piece_name = (
            chess.piece_name(
                piece.piece_type
            ).capitalize()
            if piece
            else "Piece"
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

        board_proxy_history.append(
            {
                "from":
                "BoardProxy",

                "to":
                "Player Agent",

                "message":
                move_text
            }
        )

        return move_text

    except Exception as e:

        return str(e)


# =====================================
# CREATE AGENTS
# =====================================
def create_agents():

    # -------------------------
    # BOARD PROXY
    # -------------------------
    board_proxy = (
        ConversableAgent(
            name=
            "BoardProxy",

            llm_config=
            False,

            human_input_mode=
            "NEVER",

            code_execution_config=
            False,
        )
    )

    # -------------------------
    # WHITE PLAYER
    # -------------------------
    player_white = (
        ConversableAgent(
            name=
            "PlayerWhite",

            system_message=
            (
                "You are a chess player "
                "playing as white.\n\n"

                "IMPORTANT RULES:\n"
                "1. Always call "
                "get_legal_moves() "
                "first.\n"

                "2. Choose ONE move "
                "from the legal moves.\n"

                "3. Call "
                "make_move(move).\n"

                "4. After moving, "
                "say one short fun "
                "chess comment."
            ),

            llm_config=
            llm_config,

            human_input_mode=
            "NEVER",
        )
    )

    # -------------------------
    # BLACK PLAYER
    # -------------------------
    player_black = (
        ConversableAgent(
            name=
            "PlayerBlack",

            system_message=
            (
                "You are a chess player "
                "playing as black.\n\n"

                "IMPORTANT RULES:\n"
                "1. Always call "
                "get_legal_moves() "
                "first.\n"

                "2. Choose ONE move "
                "from legal moves.\n"

                "3. Call "
                "make_move(move).\n"

                "4. After moving, "
                "say one short fun "
                "chess comment."
            ),

            llm_config=
            llm_config,

            human_input_mode=
            "NEVER",
        )
    )

    # -------------------------
    # REGISTER TOOLS
    # -------------------------
    for player in [
        player_white,
        player_black
    ]:

        player.register_for_llm(
            name=
            "get_legal_moves",

            description=
            "Get legal chess moves."
        )(
            get_legal_moves
        )

        player.register_for_llm(
            name=
            "make_move",

            description=
            "Make a chess move."
        )(
            make_move
        )

    board_proxy.register_for_execution(
        name=
        "get_legal_moves"
    )(
        get_legal_moves
    )

    board_proxy.register_for_execution(
        name=
        "make_move"
    )(
        make_move
    )

    return (
        player_white,
        player_black,
        board_proxy
    )


# =====================================
# RUN GAME
# =====================================
def run_game(
    turns=4
):

    (
        player_white,
        player_black,
        board_proxy,
    ) = create_agents()

    result = (
        player_black
        .initiate_chat(
            recipient=
            player_white,

            message=
            (
                "Let's play chess! "
                "Your move."
            ),

            max_turns=
            turns,

            summary_method=
            "last_msg",
        )
    )

    chat_history = []

    for msg in (
        result.chat_history
    ):

        role = msg.get(
            "name"
        )

        content = msg.get(
            "content",
            ""
        )

        if (
            role
            and content
        ):

            chat_history.append(
                {
                    "name":
                    role,

                    "content":
                    content,
                }
            )

    return {
        "chat_history":
        chat_history
    }


# =====================================
# GET BOARD SVG
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

    return (
        agent_interactions
    )


def get_board_proxy_history():

    return (
        board_proxy_history
    )