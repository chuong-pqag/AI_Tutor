from dataclasses import dataclass
from typing import Optional

@dataclass
class HocSinh:
    id: str
    ho_ten: str
    lop: int
    email: Optional[str] = None

@dataclass
class KetQuaTest:
    id: str
    hoc_sinh_id: str
    mon: str
    lop: int
    tuan: int
    diem: float
    ngay_test: str

@dataclass
class ChuDe:
    id: str
    mon: str
    lop: int
    tuan: int
    ten_chu_de: str
    mo_ta: str
    video_url: str
