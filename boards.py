"""板块定义：SIC 码 → 细分板块（每个板块对应一个参考 ETF）→ 11 个大类行业。

SIC 是 SEC 的行业码，比 GICS 粗、个别大名字分得不对（AMZN = 邮购零售、V/MA = 商业服务），
所以 OVERRIDE 里按代码手工改；改动只在这里，不在 build.py 里。
"""
from __future__ import annotations

# 大类行业（显示顺序）
SECTORS = [
    ("TECH", "信息技术", "XLK"),
    ("COMM", "通信服务", "XLC"),
    ("DISC", "可选消费", "XLY"),
    ("HLTH", "医疗保健", "XLV"),
    ("FIN", "金融", "XLF"),
    ("INDU", "工业", "XLI"),
    ("ENGY", "能源", "XLE"),
    ("MATL", "原材料", "XLB"),
    ("STPL", "必需消费", "XLP"),
    ("UTIL", "公用事业", "XLU"),
    ("REAL", "房地产", "XLRE"),
    ("OTHR", "其他", ""),
]

# 板块：code -> (中文名, 参考 ETF, 大类)
BOARDS = {
    "SEMI": ("半导体", "SMH", "TECH"),
    "SOFT": ("软件", "IGV", "TECH"),
    "HARD": ("硬件与网络设备", "XLK", "TECH"),
    "ELEC": ("电子元件与仪器", "XLK", "TECH"),
    "ITSV": ("IT 服务与数据处理", "XLK", "TECH"),
    "INET": ("互联网平台", "FDN", "COMM"),
    "MEDIA": ("媒体与娱乐", "XLC", "COMM"),
    "TELE": ("电信", "IYZ", "COMM"),
    "ECOM": ("电商", "IBUY", "DISC"),
    "AUTO": ("汽车与零部件", "CARZ", "DISC"),
    "RETL": ("零售", "XRT", "DISC"),
    "APPL": ("服装鞋履与奢侈品", "XLY", "DISC"),
    "LEIS": ("酒店餐饮与休闲", "PEJ", "DISC"),
    "HOME": ("住宅建筑", "ITB", "DISC"),
    "PHRM": ("制药", "IHE", "HLTH"),
    "BIO": ("生物科技", "XBI", "HLTH"),
    "MDEV": ("医疗器械与生命科学工具", "IHI", "HLTH"),
    "HCSV": ("医疗服务与保险", "IHF", "HLTH"),
    "BANK": ("银行", "KBE", "FIN"),
    "CAPM": ("券商、资管与交易所", "IAI", "FIN"),
    "INSR": ("保险", "KIE", "FIN"),
    "PAY": ("支付与消费金融", "IPAY", "FIN"),
    "CRYP": ("加密相关", "BITQ", "FIN"),
    "AERO": ("航空航天与国防", "ITA", "INDU"),
    "MACH": ("机械与电气设备", "XLI", "INDU"),
    "TRAN": ("交通运输", "IYT", "INDU"),
    "AIRL": ("航空公司", "JETS", "INDU"),
    "CONS": ("建筑与工程", "PAVE", "INDU"),
    "BSVC": ("商业服务", "XLI", "INDU"),
    "OILP": ("油气开采", "XOP", "ENGY"),
    "OILS": ("油服", "OIH", "ENGY"),
    "OILI": ("综合油气、炼化与中游", "XLE", "ENGY"),
    "URAN": ("煤炭与铀", "URA", "ENGY"),
    "GOLD": ("黄金与贵金属矿业", "GDX", "MATL"),
    "METL": ("金属与采矿", "XME", "MATL"),
    "CHEM": ("化工、包装与建材", "XLB", "MATL"),
    "FOOD": ("食品饮料与烟草", "PBJ", "STPL"),
    "HHPC": ("家庭与个人用品", "XLP", "STPL"),
    "SRTL": ("必需品零售", "XLP", "STPL"),
    "UTIL": ("公用事业", "XLU", "UTIL"),
    "REIT": ("REIT 与地产", "XLRE", "REAL"),
    "OTHR": ("未归类", "", "OTHR"),
}

# SIC 区间 -> 板块。按顺序匹配，先写的优先（细的在前，粗的在后）。
RANGES = [
    # 能源
    ((1311, 1311), "OILP"), ((1381, 1389), "OILS"), ((3533, 3533), "OILS"),
    ((2911, 2999), "OILI"), ((4610, 4619), "OILI"), ((4920, 4925), "OILI"), ((5171, 5172), "OILI"),
    ((1220, 1241), "URAN"), ((1090, 1099), "URAN"),
    # 原材料
    ((1040, 1044), "GOLD"), ((1000, 1039), "METL"), ((1045, 1089), "METL"), ((1400, 1499), "CHEM"),
    ((3310, 3399), "METL"), ((5050, 5052), "METL"),
    ((2833, 2834), "PHRM"), ((2835, 2836), "BIO"),
    ((2840, 2844), "HHPC"), ((2676, 2676), "HHPC"),
    ((2800, 2899), "CHEM"), ((2600, 2699), "CHEM"), ((3080, 3089), "CHEM"), ((3200, 3299), "CHEM"),
    ((3411, 3412), "CHEM"), ((3220, 3221), "CHEM"), ((2400, 2499), "CHEM"),
    # 必需消费
    ((2000, 2199), "FOOD"), ((5140, 5149), "FOOD"), ((5180, 5182), "FOOD"), ((100, 999), "FOOD"),
    ((5331, 5331), "SRTL"), ((5399, 5399), "SRTL"), ((5400, 5499), "SRTL"), ((5912, 5912), "SRTL"),
    # 医疗
    ((3841, 3851), "MDEV"), ((3826, 3826), "MDEV"), ((5047, 5047), "MDEV"), ((8071, 8071), "MDEV"),
    ((8731, 8731), "BIO"),
    ((6324, 6324), "HCSV"), ((8000, 8099), "HCSV"), ((5122, 5122), "HCSV"),
    # 信息技术
    ((3674, 3674), "SEMI"), ((3559, 3559), "SEMI"),
    ((7371, 7372), "SOFT"),
    ((3570, 3579), "HARD"), ((3661, 3669), "HARD"),
    ((3670, 3699), "ELEC"), ((3820, 3829), "ELEC"), ((3600, 3609), "ELEC"), ((5045, 5045), "ELEC"),
    ((5065, 5065), "ELEC"),
    ((7373, 7379), "ITSV"),
    # 通信 / 互联网
    ((7370, 7370), "INET"),
    ((4810, 4813), "TELE"), ((4899, 4899), "TELE"), ((4820, 4822), "TELE"),
    ((4830, 4841), "MEDIA"), ((7810, 7841), "MEDIA"), ((2710, 2799), "MEDIA"), ((7900, 7999), "LEIS"),
    # 可选消费
    ((5961, 5961), "ECOM"),
    ((3711, 3716), "AUTO"), ((3751, 3751), "AUTO"), ((5500, 5599), "AUTO"), ((7510, 7519), "AUTO"),
    ((3010, 3011), "AUTO"),
    ((1520, 1531), "HOME"), ((2451, 2452), "HOME"),
    ((2300, 2399), "APPL"), ((3020, 3021), "APPL"), ((3100, 3199), "APPL"), ((3911, 3915), "APPL"),
    ((5600, 5699), "APPL"), ((5130, 5139), "APPL"),
    ((5812, 5813), "LEIS"), ((7000, 7099), "LEIS"), ((4400, 4499), "TRAN"),
    ((5200, 5999), "RETL"), ((2500, 2599), "RETL"), ((3630, 3639), "RETL"), ((3940, 3949), "RETL"),
    # 金融
    ((6020, 6039), "BANK"), ((6000, 6019), "BANK"), ((6100, 6111), "BANK"), ((6035, 6036), "BANK"),
    ((6162, 6163), "BANK"), ((6712, 6712), "BANK"),
    ((6140, 6159), "PAY"),
    ((6798, 6798), "REIT"), ((6500, 6599), "REIT"),   # 地产（6798 必须在 CAPM 6722–6799 之前）
    ((6200, 6299), "CAPM"), ((6722, 6799), "CAPM"), ((6199, 6199), "CAPM"),
    ((6300, 6411), "INSR"),
    # 工业
    ((3720, 3729), "AERO"), ((3760, 3769), "AERO"), ((3812, 3812), "AERO"), ((3730, 3732), "AERO"),
    ((3480, 3489), "AERO"),
    ((4512, 4512), "AIRL"),
    ((4000, 4299), "TRAN"), ((4500, 4599), "TRAN"), ((4700, 4799), "TRAN"), ((3740, 3743), "TRAN"),
    ((1500, 1799), "CONS"), ((8711, 8711), "CONS"),
    ((3400, 3569), "MACH"), ((3580, 3599), "MACH"), ((3610, 3629), "MACH"), ((3640, 3660), "MACH"),
    ((3790, 3799), "MACH"), ((5000, 5099), "MACH"),
    # 公用事业
    ((4900, 4999), "UTIL"),
    ((7300, 7399), "BSVC"), ((8700, 8799), "BSVC"), ((8200, 8399), "BSVC"), ((7600, 7699), "BSVC"),
]

# 按代码手工改（SIC 明显不符合交易员的板块认知的大名字）
OVERRIDE = {
    # 电商 / 互联网
    "AMZN": "ECOM", "BABA": "ECOM", "PDD": "ECOM", "JD": "ECOM", "MELI": "ECOM", "SHOP": "ECOM",
    "SE": "ECOM", "CPNG": "ECOM", "EBAY": "ECOM", "ETSY": "ECOM", "CHWY": "ECOM", "W": "ECOM",
    "GOOGL": "INET", "GOOG": "INET", "META": "INET", "BIDU": "INET", "PINS": "INET", "SNAP": "INET",
    "RDDT": "INET", "TCEHY": "INET", "UBER": "INET", "LYFT": "INET", "DASH": "INET", "ABNB": "INET",
    "BKNG": "INET", "EXPE": "INET", "NFLX": "MEDIA", "SPOT": "MEDIA", "ROKU": "MEDIA", "DIS": "MEDIA",
    "TTD": "SOFT", "APP": "SOFT",
    # 支付 / 消费金融 / 加密
    "V": "PAY", "MA": "PAY", "PYPL": "PAY", "AXP": "PAY", "COF": "PAY", "SYF": "PAY", "XYZ": "PAY",
    "AFRM": "PAY", "SOFI": "PAY", "UPST": "PAY", "FI": "PAY", "FISV": "PAY", "FIS": "PAY", "GPN": "PAY",
    "TOST": "PAY", "NU": "PAY", "ALLY": "PAY", "DFS": "PAY",
    "COIN": "CRYP", "MSTR": "CRYP", "MARA": "CRYP", "RIOT": "CRYP", "CLSK": "CRYP", "HUT": "CRYP",
    "CIFR": "CRYP", "IREN": "CRYP", "WULF": "CRYP", "BTDR": "CRYP", "CORZ": "CRYP", "BITF": "CRYP",
    "GLXY": "CRYP", "CRCL": "CRYP", "BMNR": "CRYP", "SBET": "CRYP", "BLSH": "CRYP", "GEMI": "CRYP",
    "HOOD": "CAPM",
    # 半导体（设备、EDA 以外的）
    "AMAT": "SEMI", "LRCX": "SEMI", "KLAC": "SEMI", "ASML": "SEMI", "TER": "SEMI", "ONTO": "SEMI",
    "ENTG": "SEMI", "MKSI": "SEMI", "NVMI": "SEMI", "CAMT": "SEMI", "AMKR": "SEMI", "ACLS": "SEMI",
    "COHU": "SEMI", "FORM": "SEMI", "KLIC": "SEMI", "UCTT": "SEMI", "ICHR": "SEMI", "AEHR": "SEMI",
    # 硬件 / 网络
    "AAPL": "HARD", "ANET": "HARD", "CSCO": "HARD", "DELL": "HARD", "HPE": "HARD", "SMCI": "HARD",
    # 汽车
    "TSLA": "AUTO", "RIVN": "AUTO", "LCID": "AUTO", "NIO": "AUTO", "XPEV": "AUTO", "LI": "AUTO",
    # 必需品零售（GICS 口径）
    "WMT": "SRTL", "COST": "SRTL", "TGT": "SRTL", "DG": "SRTL", "DLTR": "SRTL", "BJ": "SRTL",
    "KR": "SRTL", "ACI": "SRTL",
    # 医疗
    "TMO": "MDEV", "DHR": "MDEV", "A": "MDEV", "IQV": "MDEV", "ILMN": "MDEV", "WAT": "MDEV",
    "MTD": "MDEV", "CVS": "HCSV",
    # 能源 / 电力
    "CCL": "LEIS", "RCL": "LEIS", "NCLH": "LEIS", "VIK": "LEIS",
    "XOM": "OILI", "CVX": "OILI", "CCJ": "URAN", "UEC": "URAN", "LEU": "URAN", "OKLO": "UTIL",
    "SMR": "MACH", "NNE": "MACH",
    "GEV": "MACH", "VRT": "MACH", "ETN": "MACH",
    # 工业
    "FDX": "TRAN", "UPS": "TRAN", "URI": "BSVC", "WM": "BSVC", "RSG": "BSVC",
    "RKLB": "AERO", "ASTS": "TELE", "LUNR": "AERO", "PL": "AERO",
    # 其他明显的
    "IBM": "ITSV", "ACN": "ITSV", "PLTR": "SOFT",
    # 2026-11-23 第一版抽查后补（SIC 与 GICS 认知不符）
    "CDW": "ITSV", "SHW": "CHEM", "FAST": "MACH", "KMB": "HHPC", "HL": "GOLD", "ECL": "CHEM",
    "FIVE": "RETL", "OLLI": "RETL", "CASY": "SRTL",
    "SPGI": "CAPM", "MCO": "CAPM", "MSCI": "CAPM", "FICO": "SOFT", "TRI": "BSVC",
    "AKAM": "ITSV", "CART": "INET", "GRAB": "INET", "FTAI": "TRAN", "GEO": "BSVC", "ECG": "CONS",
    "CRL": "MDEV", "IDXX": "MDEV", "ABT": "MDEV", "HNGE": "HCSV", "TEM": "HCSV",
    "GE": "AERO", "HWM": "AERO", "SPCX": "AERO", "HONA": "AERO",
    "TT": "MACH", "EMR": "MACH", "ROK": "MACH", "AME": "MACH", "OTIS": "MACH", "HUBB": "MACH",
    "NXT": "MACH", "ROP": "SOFT", "GLW": "ELEC",
    "WDAY": "SOFT", "IOT": "SOFT", "DOCN": "ITSV", "ZM": "SOFT",
    "PANW": "SOFT", "FTNT": "SOFT", "QCOM": "SEMI",
    "CTAS": "BSVC", "WCN": "BSVC", "SHEL": "OILI", "PBR": "OILI",
}


def board_of(ticker: str, sic: str) -> str:
    if ticker in OVERRIDE:
        return OVERRIDE[ticker]
    try:
        s = int(sic)
    except (TypeError, ValueError):
        return "OTHR"
    for (lo, hi), b in RANGES:
        if lo <= s <= hi:
            return b
    return "OTHR"
