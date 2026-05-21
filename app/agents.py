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
) -> str:

    chess_move = (
        chess.Move
        .from_uci(move)
    )

    board.push_uci(
        str(chess_move)
    )

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
                "playing as white. "
                "Always first call "
                "get_legal_moves(). "
                "Then select ONE move "
                "and call "
                "make_move(move). "
                "After your move, "
                "make short fun chitchat."
            ),

            llm_config=
            llm_config,

            human_input_mode=
            "NEVER",
        )
    )

    player_black = (
        ConversableAgent(
            name=
            "PlayerBlack",

            system_message=
            (
                "You are a chess player "
                "playing as black. "
                "Always first call "
                "get_legal_moves(). "
                "Then select ONE move "
                "and call "
                "make_move(move). "
                "After your move, "
                "make short fun chitchat."
            ),

            llm_config=
            llm_config,

            human_input_mode=
            "NEVER",
        )
    )

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

    for caller in [
        player_white,
        player_black
    ]:

        register_function(
            get_legal_moves,

            caller=
            caller,

            executor=
            board_proxy,

            name=
            "get_legal_moves",

            description=
            "Get legal chess moves."
        )

        register_function(
            make_move,

            caller=
            caller,

            executor=
            board_proxy,

            name=
            "make_move",

            description=
            "Make a chess move."
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
        board_proxy
    ) = create_agents()

    all_messages = []

    current_player = (
        player_white
    )

    for turn in range(
        turns
    ):

        result = (
            current_player
            .generate_reply(
                messages=[
                    {
                        "role":
                        "user",

                        "content":
                        "Make one legal chess move."
                    }
                ]
            )
        )

        all_messages.append(
            {
                "name":
                current_player.name,

                "content":
                result,
            }
        )

        board_proxy_history.append(
            {
                "from":
                "BoardProxy",

                "to":
                current_player.name,

                "message":
                (
                    "Executed chess tools "
                    "for move selection."
                )
            }
        )

        current_player = (
            player_black
            if current_player
            == player_white
            else
            player_white
        )

    return {
        "chat_history":
        all_messages
    }


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