import enum
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pygments.lexers.supercollider import SuperColliderLexer
from pygments.token import _TokenType


class ScType(enum.Enum):
    sc_class = "class"
    function = "function"
    variable = "variable"


@dataclass
class ScToken:
    token_type: _TokenType
    name: str


@dataclass
class ScAst:
    sc_type: ScType
    name: str
    children: List["ScAst"]
    value: str


@dataclass
class ScAstNode:
    pass


class SuperColliderParser:
    def __init__(self, sc_tokens: List[ScToken]) -> None:
        self.current_index: int = 0
        self.text: str
        self.sc_tokens: List[ScToken] = sc_tokens

    @classmethod
    def from_file(cls, file_path: Path):
        with file_path.open("r") as f:
            text = f.read()

        sc_tokens: List[ScToken] = []
        for token, name in SuperColliderLexer().get_tokens(text):
            sc_tokens.append(
                ScToken(
                    token_type=token,
                    name=name,
                )
            )

        p = cls(sc_tokens)
        p._build_ast()
        return p

    def _process(self) -> Optional[ScAstNode]:
        current_token = self.sc_tokens[self.current_index]
        self.current_index += 1

        if current_token.token_type:
            pass

        return None

    def _build_ast(self) -> None:
        children: List[ScAstNode] = []

        while self.current_index < len(self.sc_tokens):
            next = self._process()

            if next:
                children.append(next)

        return
