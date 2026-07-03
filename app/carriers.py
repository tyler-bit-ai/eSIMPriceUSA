from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CarrierDefinition:
    code: str
    label: str
    aliases: tuple[str, ...]


COUNTRY_CARRIER_REGISTRY: dict[str, tuple[CarrierDefinition, ...]] = {
    "kr": (
        CarrierDefinition(code="skt", label="SKT", aliases=("skt", "sk telecom", "sktelecom")),
        CarrierDefinition(code="kt", label="KT", aliases=("kt", "kt olleh", "olleh")),
        CarrierDefinition(code="lgu", label="LGU+", aliases=("lg u+", "lgu+", "uplus", "lg u plus", "lgu")),
    ),
    "vn": (
        CarrierDefinition(code="viettel", label="Viettel", aliases=("viettel",)),
        CarrierDefinition(code="vinaphone", label="VinaPhone", aliases=("vinaphone", "vina phone", "vnpt")),
        CarrierDefinition(code="mobifone", label="MobiFone", aliases=("mobifone", "mobi phone")),
        CarrierDefinition(code="vietnamobile", label="Vietnamobile", aliases=("vietnamobile", "vietnam mobile")),
    ),
    "tw": (
        CarrierDefinition(code="chunghwa", label="Chunghwa Telecom", aliases=("chunghwa", "中華電信", "cht")),
        CarrierDefinition(code="taiwan_mobile", label="Taiwan Mobile", aliases=("taiwan mobile", "台灣大哥大", "twm")),
        CarrierDefinition(code="fareastone", label="Far EasTone", aliases=("far eas tone", "far eastone", "遠傳", "fet")),
    ),
    "hk": (
        CarrierDefinition(code="cmhk", label="CMHK", aliases=("cmhk", "china mobile hong kong", "中國移動香港")),
        CarrierDefinition(code="csl", label="CSL", aliases=("csl", "one2free", "1o1o", "pccw-hkt")),
        CarrierDefinition(code="smartone", label="SmarTone", aliases=("smartone", "smart one")),
        CarrierDefinition(code="three_hk", label="3HK", aliases=("3hk", "3 hong kong", "three hk")),
    ),
    "mo": (
        CarrierDefinition(code="ctm", label="CTM", aliases=("ctm", "macau telecom", "澳門電訊")),
        CarrierDefinition(code="china_telecom_macau", label="China Telecom (Macau)", aliases=("china telecom macau", "中國電信澳門", "中國電信", "ctm macau")),
        CarrierDefinition(code="three_macau", label="3 Macau", aliases=("3 macau", "three macau", "hutchison telephone macau")),
    ),
    "th": (
        CarrierDefinition(code="ais", label="AIS", aliases=("ais", "advanced info service")),
        CarrierDefinition(code="dtac", label="dtac", aliases=("dtac",)),
        CarrierDefinition(code="truemove", label="TrueMove H", aliases=("truemove", "truemove h", "true move")),
    ),
    "jp": (
        CarrierDefinition(code="docomo", label="NTT docomo", aliases=("docomo", "ntt docomo", "ドコモ")),
        CarrierDefinition(code="au", label="au (KDDI)", aliases=("au", "kddi", "au by kddi")),
        CarrierDefinition(code="softbank", label="SoftBank", aliases=("softbank", "soft bank", "ソフトバンク")),
        CarrierDefinition(code="rakuten", label="Rakuten Mobile", aliases=("rakuten mobile", "rakuten", "楽天モバイル")),
    ),
}


def get_country_carriers(country: str | None) -> tuple[CarrierDefinition, ...]:
    if not country:
        return ()
    return COUNTRY_CARRIER_REGISTRY.get(country, ())


def get_country_carrier_codes(country: str | None) -> list[str]:
    return [carrier.code for carrier in get_country_carriers(country)]


def get_country_carrier_labels(country: str | None) -> dict[str, str]:
    return {carrier.code: carrier.label for carrier in get_country_carriers(country)}


def get_carrier_metadata() -> dict[str, list[dict[str, object]]]:
    return {
        country: [asdict(carrier) for carrier in carriers]
        for country, carriers in COUNTRY_CARRIER_REGISTRY.items()
    }
