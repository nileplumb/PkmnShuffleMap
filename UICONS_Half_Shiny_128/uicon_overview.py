"""
Script made by Malte/ccev to analyze missing Pokemon Icons in a UICON iconset.

- Install pogodata (pip install pogodata)
- Copy this script to the root directory of your UICONS repo
- Run it
- It should create a file named index.html you can then open
"""

import os
import requests
from pogodata import PogoData

master = requests.get("https://api.github.com/repos/PokeMiners/pogo_assets/branches/master").json()
sha = master["commit"]["sha"]
icons = requests.get(f"https://api.github.com/repos/PokeMiners/pogo_assets/git/trees/{sha}?recursive=true")
icons = icons.json()["tree"]
ingame_icons = [i["path"].replace(".png", "").replace("Images/Pokemon/", "") for i in icons]

pogodata = PogoData()
costumes = pogodata.get_enum("Costume", reverse=True)
existing_assets = set()
index = set()


def name_to_attr(parts: list, flag: str) -> int:
    for part in parts:
        if part.startswith(flag):
            return int(part[1:])
    return 0


def uicon_to_mon(uicon: str):
    parts = uicon.split("_")

    mon_id = int(parts[0])
    mega_id = name_to_attr(parts, "e")
    form_id = name_to_attr(parts, "f")
    costume_id = name_to_attr(parts, "c")
    gender_id = name_to_attr(parts, "g")

    mon = pogodata.get_mon(id=mon_id, temp_evolution_id=mega_id, form=form_id,
                           costume=costume_id)

    return mon


def get_uicons(mon, is_shiny=False):
    ids = [str(mon.id), ""]

    if mon.temp_evolution_id > 0:
        megas = ["_e" + str(mon.temp_evolution_id), ""]
    else:
        megas = [""]

    if mon.form > 0:
        forms = ["_f" + str(mon.form), ""]
    else:
        forms = [""]

    if mon.costume > 0:
        costumes = ["_c" + str(mon.costume), ""]
    else:
        costumes = [""]

    if is_shiny:
        shiny = ["_s", ""]
    else:
        shiny = [""]

    full_uicon = ids[0] + megas[0] + forms[0] + costumes[0] + shiny[0]

    for monid in ids:
        for mega in megas:
            for form in forms:
                for costume in costumes:
                    for is_shiny in shiny:
                        icon = monid + mega + form + costume + is_shiny
                        if icon in index:
                            return icon, full_uicon

    return None, full_uicon


for file in os.scandir("pokemon"):
    filename = file.name.split(".")[0]
    if filename == "index":
        continue
    index.add(filename)
    try:
        mon = uicon_to_mon(filename)
        if filename.endswith("_s"):
            shiny = "_shiny"
        else:
            shiny = ""
        existing_assets.add(mon.asset+shiny)
    except Exception as e:
        print(f"Couldn't handle {filename}")
        print(e)
        continue


class HTML:
    def __init__(self):
        self.status = {
            "FULL": {
                "icon": "check",
                "color": "green",
                "name": "full",
                "desc": "The Pokemon is represented correctly and no fallback was needed"
            },
            "FALLBACK": {
                "icon": "minus",
                "color": "green",
                "name": "fallback",
                "desc": "When the icon represents the correct Pokemon, but fallback was used. "
                        "(e.g. you want to display Purified Pikachu but the icon of normal Pikachu is used)"
            },
            "DEFAULT": {
                "icon": "times",
                "color": "orange",
                "name": "overlay",
                "desc": "When the base Mon is the same, but an overlay (like a costume) is missing. "
                        "(e.g. you want to display Party hat Bulbasaur but the icon of normal Bulbasaur is used)<br>"
                        "<i>Warning: This is faulty for some Pokemon like FALL_2018 Pichu, 1st-form Spinda, "
                        "trash-form Wormadam, standard Darmanitan and Galar evolutions like Obstagoon, Perrserker, "
                        "Sirfetch’d, Mr. Rime and Runerigus</i>"
            },
            "MISSING": {
                "icon": "times",
                "color": "red",
                "name": "missing",
                "desc": "The Pokemon icon is missing and the default 0 icon is displayed"
            }
        }

        headers = ["Name", "Pokémon", "Form", "Costume", "Mega ID", "Full UICON", "Used UICON", "Status", "UICON",
                   "In-game Icon"]

        self.html = """
            <html>
            <head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
            <style>
            body {
                font-family: arial, sans-serif;
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            
            td, th {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            
            tr:nth-child(even) {
                background-color: #eeeeee;
            }
            </style>
            </head>
            <body>
            
        """

        self.html += "<h1>UICON Overview</h1>"
        self.html += "<h2>Status Legend</h2>"

        for status in self.status.values():
            icon = f'<i class="fa fa-{status["icon"]}" style="font-size:20px;' \
                   f'color:{status["color"]};"></i> <b>{status["name"]}</b>'
            self.html += f"<a>{icon}<br>{status['desc']}<br><br></a>"

        self.html += "<table><tr>"
        for header in headers:
            self.html += "<th>" + header + "</th>"
        self.html += "</tr>"

    def gen_html(self):
        for mon in sorted(pogodata.mons, key=lambda m: (m.id, m.form)):
            for shiny in (False, True):
                used_icon, full_icon = get_uicons(mon, shiny)

                if shiny:
                    mon.asset += "_shiny"

                if mon.asset not in ingame_icons:
                    continue

                icon_url = (
                    f"https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Images/Pokemon%20-%20256x256/"
                    f"{mon.asset}.png"
                )

                present = self.status["DEFAULT"]
                if mon.asset in existing_assets:
                    present = self.status["FALLBACK"]
                if used_icon == full_icon:
                    present = self.status["FULL"]
                if used_icon is None:
                    used_icon = "0"
                    present = self.status["MISSING"]

                present = f'<i class="fa fa-{present["icon"]}" style="font-size:20px;' \
                          f'color:{present["color"]};"></i> {present["name"]}'

                if mon.base_template == mon.template:
                    template = "UNSET"
                else:
                    template = mon.template
                self.html += f"""
                  <tr>
                    <td>{"Shiny " if shiny else ""} {mon.name}</td>
                    <td>{mon.base_template} ({mon.id}) {" (SHINY)" if shiny else ""}</td>
                    <td>{template} ({mon.form})</td>
                    <td>{costumes.get(mon.costume, 0)} ({mon.costume})</td>
                    <td>{mon.temp_evolution_id}</td>
                    <td>{full_icon}</td>
                    <td>{used_icon}</td>
                    <td>{present}</td>
                    <td><img src="pokemon/{used_icon}.png" width="40" height="40"></td>
                    <td>
                      <img src="{icon_url}" 
                         width="60" height="60">
                    </td>
                  </tr>
                """

        self.html += "</table></body></html>"
        return self.html


with open("index.html", "w+", encoding="utf-8") as f:
    f.write(HTML().gen_html())
print("Done.")
