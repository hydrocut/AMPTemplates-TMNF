# AMPTemplates-TMNF — TrackMania Nations Forever pour AMP

Template **AMP Generic Module** pour héberger un serveur dédié **TrackMania
Nations Forever** sur Linux. CubeCoders n'en propose aucun pour aucune version
de TrackMania.

## Pourquoi cette version-là

| Version | Hébergeable ? |
|---|---|
| Trackmania (2020) | le palier **Club** est payant ; la version gratuite ne peut pas héberger |
| TrackMania² / ManiaPlanet | les serveurs de fichiers de ManiaPlanet ne répondent plus |
| **Nations Forever** | **oui** — jeu gratuit, paquet serveur toujours en ligne |

Et c'est le serveur le plus simple du catalogue :

```
paquet officiel  : 12,5 Mo
binaire Linux    : TrackmaniaServer, ELF EXEC STATIQUE
dépendances      : aucune
```

**Statique.** Pas de `libc6:i386`, pas de `libcurl`, rien du tout. Il suffit
que le noyau sache exécuter du 32 bits. C'est plus simple que tout le reste.

## Deux choses à préparer avant de démarrer

### Un compte, et il se cree DANS LE JEU

Le serveur a besoin d'un compte pour s'identifier. Sans lui il demarre, puis
s'arrete sur :

```
ERROR: Login unknown: there is no account with this login.
```

**Ce compte se cree dans TrackMania Nations Forever**, pas sur un site : lance
le jeu, cree un nouveau profil avec un compte en ligne, note le login et le mot
de passe. Le compte sera confisque par le serveur -- il ne pourra plus servir a
jouer tant que celui-ci tourne.

**Le piege a eviter.** Le portail
<https://www.trackmania.com/player/dedicated-servers> propose de creer de vrais
comptes de serveur, et il fonctionne tres bien... pour le **Trackmania de
2020**. Les comptes qu'on y cree ne sont pas connus de l'annuaire que ce
serveur-ci interroge : on obtient `Login unknown`, verifie trois fois avec deux
comptes differents. Ce portail n'a rien a faire ici.

Le login se tape **exactement** comme il a ete cree : une majuscule de travers
suffit a le rendre introuvable.

Et si la reponse est `Please try again later` plutot que `Login unknown`, c'est
une bonne nouvelle : le compte existe, il est seulement deja connecte ailleurs
(ferme le jeu sur ton PC) ou bride quelques minutes apres des essais rates.

### Changer les trois mots de passe d'administration

Le fichier livré par Nadeo contient ceci, mot pour mot :

```xml
<level><name>SuperAdmin</name><password>SuperAdmin</password></level>
<level><name>Admin</name><password>Admin</password></level>
<level><name>User</name><password>User</password></level>
```

Tous les serveurs TrackMania de la planète partent avec ces trois mots de
passe. Le SuperAdmin donne **tous** les pouvoirs, y compris par le port
XML-RPC. Le template les expose vides dans AMP, sous *Administration*, pour
qu'on ne puisse pas les oublier.

## Un seul template pour Nations ET United

Le paquet serveur est le meme pour les deux jeux de la generation Forever, et
il contient **tous les circuits** : 65 pour Nations (Blanc, Vert, Rouge, Bleu,
Noir) et 210 pour United (Race, Platform, Puzzle, Stunts), verifies un par un
contre les 32 series de circuits livrees -- **zero manquant**.

Autrement dit : le serveur possede les sept environnements sans que personne
n'ait achete quoi que ce soit.

Ce qui change, c'est **qui a le droit d'entrer**, et cela tient a un seul
reglage, `packmask`. Le binaire le dit lui-meme :

> Defines the packmask of the server. Can be 'United', 'Nations', 'Sunrise',
> 'Original', or environment names.

| packmask | Public |
|---|---|
| `Nations` | les joueurs du jeu **gratuit** (TMNF) |
| `United` | seulement ceux qui ont achete **TrackMania United Forever** |

Le reglage decide du public, pas du contenu. Un serveur en `United` avec des
circuits de Bay ou de Coast sera superbe et desert si personne dans la
communaute n'a le jeu payant.

## Installation

### 1. Ajouter le dépôt dans ADS

Configuration → Instance Deployment → Configuration Repositories → ajouter :

```
hydrocut/AMPTemplates-TMNF:main
```

puis **Fetch Latest**.

### 2. Créer l'instance, puis Update

AMP télécharge le paquet officiel et le décompresse.

Le téléchargement se fait en **HTTP simple** : `files2.trackmaniaforever.com`
ne sert pas le HTTPS. C'est un paquet public, figé depuis 2011, mais autant le
savoir.

L'extraction est en `OverwriteExistingFiles: false`, volontairement : le paquet
n'a pas bougé depuis le 21 février 2011, donc rien n'est perdu à ne pas
réécrire — et en échange, **un Update ne peut jamais écraser ta configuration,
ta liste de circuits ou tes records**.

### 3. Régler, puis démarrer

Dans l'onglet Configuration : le compte de jeu (obligatoire), les trois mots de
passe d'administration, le nom du serveur, la série de circuits.

## Les ports

| Port | Protocole | Rôle |
|---|---|---|
| 2350 | **Both** | jeu et annonce au serveur maître — TrackMania s'en sert en TCP *et* en UDP |
| 3450 | UDP | partage des circuits entre joueurs |
| 5000 | TCP | XML-RPC, le pilotage du serveur |

Le XML-RPC reste sur la machine (`xmlrpc_allowremote` à `False`) et doit y
rester : ce port donne les pleins pouvoirs sans mot de passe de session.

## La configuration est en XML

Contrairement aux autres templates de la série, les réglages ne sont pas des
lignes `clé valeur` mais des chemins dans un document XML :

```
/dedicated/server_options/max_players
/dedicated/masterserver_account/login
/dedicated/authorization_levels/level[1]/password
```

Le dernier est le piège : les trois niveaux d'administration sont des éléments
`<level>` répétés, qui ne se distinguent que par **leur rang**. Une erreur de
rang donnerait le mot de passe SuperAdmin au niveau User.

`verifier.py` reconstruit la structure du fichier de Nadeo et vérifie que
**chaque chemin tombe sur un nœud, et un seul**, y compris que `level[1]`
désigne bien SuperAdmin. Une faute de frappe dans un chemin XML ne se voit
nulle part ailleurs : AMP afficherait le champ, on le remplirait, et la valeur
n'irait jamais dans le fichier.

```bash
python verifier.py
```

Il doit afficher `Tout est bon.`

## Et les statistiques

Le serveur seul ne garde **aucun record**. Ce qui fait vivre un serveur
TrackMania, c'est un contrôleur branché sur le port XML-RPC : records locaux
par circuit, rangs des joueurs, records mondiaux Dedimania, commandes `/top` et
`/rank` en jeu.

Le classique est **XASECO** (<https://server.xaseco.org/>), en PHP + MySQL.
C'est le chantier suivant, et c'est lui qui transformera ce serveur en
véritable serveur communautaire.

## Crédits

TrackMania est une marque de Nadeo / Ubisoft. Ce template n'est ni affilié ni
approuvé par eux, et ne contient aucun fichier du jeu : le paquet serveur est
téléchargé depuis le site officiel au moment de l'Update.
