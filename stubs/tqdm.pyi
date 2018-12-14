from typing import Iterable, Any, Union, Optional, Dict
import io


class tqdm:
    def __init__(self, iterable: Optional[Iterable[Any]] = None, desc: Optional[str] = None, total: Optional[int] = None, leave: bool = True,
                 file: Optional[io.TextIOWrapper] = None, ncols: Optional[int] = None, mininterval: float = 0.1, maxinterval: float = 10.0,
                 miniters: Optional[int] = None, ascii: Optional[bool] = None, disable: bool = False, unit: str = 'it',
                 unit_scale: Union[bool, int, float] = False, dynamic_ncols: bool = False, smoothing: float = 0.3,
                 bar_format: Optional[str] = None, initial: int = 0, position: Optional[int] = None, postfix: Optional[Dict[Any, Any]] = None,
                 unit_divisor: float = 1000, gui: bool = False) -> None:
        ...

    def update(self, n: int = 1) -> None:
        ...

    def __enter__(self) -> tqdm:
        ...

    def __exit__(self, *exc: Any) -> bool:
        ...
