# -*- coding: utf-8 -*-
"""
Contrôle du template avant de le pousser.

Ce template écrit dans un fichier **XML**, pas dans un fichier clé/valeur : les
réglages visent des chemins comme `/dedicated/server_options/max_players`. Une
faute de frappe dans un de ces chemins ne se voit nulle part — AMP affiche le
champ, l'utilisateur le remplit, et la valeur ne va simplement jamais dans le
fichier. Le serveur démarre, avec l'ancienne valeur.

Le script reconstruit donc la structure du `dedicated_cfg.txt` de Nadeo et
vérifie que **chaque chemin tombe sur un nœud, et un seul**. Y compris les
trois mots de passe d'administration, qui vivent dans des éléments `<level>`
répétés et ne se distinguent que par leur position.

    python verifier.py
"""
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ICI = os.path.dirname(os.path.abspath(__file__))
NOM = 'tmnf'
soucis = []

# La structure du fichier livré par Nadeo, reconstruite d'après le vrai
# GameData/Config/dedicated_cfg.txt du paquet officiel 2011-02-21.
SQUELETTE = """<?xml version="1.0" encoding="utf-8" ?>
<dedicated>
  <authorization_levels>
    <level><name>SuperAdmin</name><password/></level>
    <level><name>Admin</name><password/></level>
    <level><name>User</name><password/></level>
  </authorization_levels>
  <masterserver_account>
    <login/><password/><validation_key/>
  </masterserver_account>
  <server_options>
    <name/><comment/><hide_server/><max_players/><password/>
    <max_spectators/><password_spectator/><ladder_mode/>
    <ladder_serverlimit_min/><ladder_serverlimit_max/>
    <enable_p2p_upload/><enable_p2p_download/>
    <callvote_timeout/><callvote_ratio/><callvote_ratios/>
    <allow_challenge_download/><autosave_replays/>
    <autosave_validation_replays/><referee_password/>
    <referee_validation_mode/><use_changing_validation_seed/>
  </server_options>
  <system_config>
    <connection_uploadrate/><connection_downloadrate/>
    <force_ip_address/><server_port/><server_p2p_port/>
    <client_port/><bind_ip_address/><xmlrpc_port/>
    <xmlrpc_allowremote/><blacklist_url/><guestlist_filename/>
    <blacklist_filename/><packmask/><allow_spectator_relays/>
    <use_proxy/><proxy_login/><proxy_password/>
  </system_config>
</dedicated>
"""


def lire_json(nom):
    with io.open(os.path.join(ICI, nom), encoding='utf-8') as f:
        return json.load(f)


# ── 1. les JSON se parsent ───────────────────────────────────────────────────
data = {}
for nom in ['manifest.json', NOM + 'config.json', NOM + 'metaconfig.json',
            NOM + 'ports.json', NOM + 'updates.json']:
    try:
        data[nom] = lire_json(nom)
        print('ok   %-22s JSON valide' % nom)
    except Exception as e:
        soucis.append('%s : JSON invalide (%s)' % (nom, e))
if soucis:
    for s in soucis:
        print('NON  ' + s)
    sys.exit(1)

# ── 2. le .kvp ne renvoie que vers des fichiers existants ────────────────────
kvp = io.open(os.path.join(ICI, NOM + '.kvp'), encoding='utf-8').read()
for ref in re.findall(r'@IncludeJson\[([^\]]+)\]', kvp):
    if os.path.isfile(os.path.join(ICI, ref)):
        print('ok   @IncludeJson         %s' % ref)
    else:
        soucis.append('@IncludeJson[%s] : fichier absent' % ref)

for cle in ('ConfigManifest', 'MetaConfigManifest'):
    m = re.search(r'^Meta\.%s=(.+)$' % cle, kvp, re.M)
    if not m or not os.path.isfile(os.path.join(ICI, m.group(1).strip())):
        soucis.append('Meta.%s pointe sur un fichier absent' % cle)
    else:
        print('ok   Meta.%-16s %s' % (cle, m.group(1).strip()))

# ── 3. les ports ─────────────────────────────────────────────────────────────
refs = set(p['Ref'] for p in data[NOM + 'ports.json'])
m = re.search(r'^App\.PrimaryApplicationPortRef=(.+)$', kvp, re.M)
if not m or m.group(1).strip() not in refs:
    soucis.append('PrimaryApplicationPortRef ne correspond a aucun port')
else:
    print('ok   port principal        %s' % m.group(1).strip())

for s in data[NOM + 'config.json']:
    fn = s.get('FieldName', '')
    if fn.startswith('$') and fn[1:] not in refs:
        soucis.append('reglage cache %s : aucun port ne porte ce Ref' % fn)

# ── 4. chaque chemin XML tombe sur un noeud, et un seul ──────────────────────
racine = ET.fromstring(SQUELETTE)
vus = {}
for s in data[NOM + 'config.json']:
    chemin = s.get('ParamFieldName', '')
    if s.get('IncludeInCommandLine'):
        continue  # celui-la part sur la ligne de commande, pas dans le XML
    if not chemin.startswith('/'):
        soucis.append('%r : chemin XML attendu, absolu' % chemin)
        continue
    vus[chemin] = vus.get(chemin, 0) + 1
    morceaux = chemin.strip('/').split('/')
    if morceaux[0] != racine.tag:
        soucis.append('%s : ne commence pas par <%s>' % (chemin, racine.tag))
        continue
    trouves = racine.findall('./' + '/'.join(morceaux[1:]))
    if len(trouves) != 1:
        soucis.append('%s : %d noeud(s) au lieu d\'un' % (chemin, len(trouves)))

doubles = [c for c, n in vus.items() if n > 1]
if doubles:
    soucis.append('chemins en double : %s' % ', '.join(doubles))
if not soucis:
    print('ok   chemins XML           %d chemins, tous uniques et resolus' % len(vus))

# les trois mots de passe d'administration ne se distinguent QUE par leur rang
for rang, attendu in ((1, 'SuperAdmin'), (2, 'Admin'), (3, 'User')):
    n = racine.findall('./authorization_levels/level[%d]/name' % rang)
    if len(n) != 1 or n[0].text != attendu:
        soucis.append('level[%d] ne designe pas %s' % (rang, attendu))
    else:
        print('ok   level[%d]              %s' % (rang, attendu))

# ── 5. le .kvp est complet ───────────────────────────────────────────────────
ATTENDUES = ['App.SupportsUniversalSleep', 'App.WakeupMode', 'App.ApplicationReadyMode',
             'Console.FilterMatchRegex', 'Console.FilterMatchReplacement',
             'Console.ThrowawayMessageRegex', 'Console.AppReadyRegex',
             'Console.UserJoinRegex', 'Console.UserLeaveRegex', 'Console.UserChatRegex',
             'Console.UpdateAvailableRegex', 'Console.PreConnectRegex',
             'Console.ConnectIPRegex', 'Console.MetricsRegex', 'Console.HideFromConsoleRegex',
             'Console.SuppressLogAtStart', 'Console.UserActions',
             'Limits.SleepMode', 'Limits.SleepOnStart', 'Limits.SleepDelayMinutes',
             'Limits.DozeDelay', 'Limits.AutoRetryCount', 'Limits.SleepStartThresholdSeconds']
absentes = [c for c in ATTENDUES if (c + '=') not in kvp]
if absentes:
    soucis.append('cles absentes du .kvp (%d) : %s' % (len(absentes), ', '.join(absentes)))
else:
    print('ok   kvp complet           les %d cles Console/Limits sont la' % len(ATTENDUES))

m = re.search(r'^App\.ApplicationReadyMode=(.+)$', kvp, re.M)
r = re.search(r'^Console\.AppReadyRegex=(.*)$', kvp, re.M)
if m and m.group(1).strip() == 'RegexMatch' and not (r and r.group(1).strip()):
    soucis.append('ApplicationReadyMode=RegexMatch mais AppReadyRegex est vide')
else:
    print('ok   mode de demarrage     %s' % (m.group(1).strip() if m else '?'))

# ── verdict ──────────────────────────────────────────────────────────────────
print()
if soucis:
    print('%d probleme(s) :' % len(soucis))
    for s in soucis:
        print('  NON  ' + s)
    sys.exit(1)
print('Tout est bon.')
