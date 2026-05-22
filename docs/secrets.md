# GitHub Secrets

Wachtwoorden, tokens en hostadressen staan niet in deze repository. Ze
worden als GitHub Secrets opgeslagen en door de workflows als environment
variables (of via een tijdelijk bestand voor het OpenVPN-profiel) aan
Ansible en OpenVPN doorgegeven. De Ansible-inventory leest deze
variabelen met `lookup('env', ...)`.

## Benodigde secrets

| Secret                  | Doel                                                         |
|-------------------------|--------------------------------------------------------------|
| `VPN_PROFILE`           | OpenVPN `.ovpn` profielinhoud waarmee RUNNER01 het           |
|                         | beheersegment bereikt                                         |
| `VPN_USERNAME`          | OpenVPN gebruikersnaam                                       |
| `VPN_PASSWORD`          | OpenVPN wachtwoord                                           |
| `SUDO_PASSWORD`         | Sudo-wachtwoord van de self-hosted runner user voor          |
|                         | installatie van packages en het starten van OpenVPN          |
| `ARISTA_API_USERNAME`   | Gebruiker voor Arista eAPI (HTTPS), bv. `admin`              |
| `ARISTA_API_PASSWORD`   | Wachtwoord voor Arista eAPI                                  |
| `ARISTA_SLEAF01_HOST`   | IP of FQDN van SLEAF01 (echt: 172.19.1.4)                    |
| `ARISTA_SLEAF02_HOST`   | IP of FQDN van SLEAF02 (echt: 172.19.1.5)                    |
| `ARISTA_SLEAF03_HOST`   | IP of FQDN van SLEAF03 (echt: 172.19.1.6)                    |
| `FORTIGATE_HOST`        | IP of FQDN van de FortiGate management-interface             |
| `FORTIGATE_API_TOKEN`   | API-token voor de FortiGate REST API                         |

## Concrete waarden

- `ARISTA_SLEAF01_HOST = 172.19.1.4`
- `ARISTA_SLEAF02_HOST = 172.19.1.5`
- `ARISTA_SLEAF03_HOST = 172.19.1.6`
- `ARISTA_API_USERNAME = admin`
- `ARISTA_API_PASSWORD` – wachtwoord uitsluitend als GitHub Secret, niet
  in Git.
- `ARISTA_API_USERNAME` en `ARISTA_API_PASSWORD` moeten geldig zijn voor
  Arista eAPI (`https://<leaf>:443/command-api`). Een HTTP 401 in de
  deployment preview betekent dat deze credentials niet kloppen voor de
  gekozen GitHub Environment of geen eAPI-toegang hebben.
- `FORTIGATE_HOST` en `FORTIGATE_API_TOKEN` – uitsluitend als GitHub
  Secret, niet in Git.
- `SUDO_PASSWORD` – sudo-wachtwoord van de runner user, uitsluitend als
  GitHub Secret. Als secrets per GitHub Environment worden beheerd, voeg
  dit secret toe aan elke environment waarop deployment of rollback draait
  (`test`, `acceptance`, `production`).

Voor `VPN_PROFILE` moet het volledige `.ovpn` bestand met echte newlines
worden opgeslagen. De veiligste manier zonder base64 is via de GitHub CLI:

```bash
gh secret set VPN_PROFILE --env test < client.ovpn
gh secret set VPN_PROFILE --env acceptance < client.ovpn
gh secret set VPN_PROFILE --env production < client.ovpn
```

Gebruik je de GitHub webinterface, open dan het `.ovpn` bestand in een editor,
selecteer de volledige inhoud en plak die rechtstreeks in de secret-waarde. De
regelafbrekingen moeten behouden blijven; plak het profiel niet als één lange
regel.

## Hoe ze worden gebruikt

- In `.github/workflows/deploy.yml` en `.github/workflows/rollback.yml`
  worden de Arista- en FortiGate-secrets in de job-`env` geïnjecteerd
  als omgevingsvariabelen met dezelfde naam.
- `VPN_PROFILE` wordt vanuit de workflow-omgeving naar `vpn.ovpn` geschreven,
  `VPN_USERNAME`/`VPN_PASSWORD` worden samen naar `vpn-auth.txt`
  geschreven. Beide bestanden krijgen mode `600`, en worden in de
  laatste stap (`if: always()`) opgeruimd. `.gitignore` voorkomt dat
  ze ooit gecommit worden.
- `SUDO_PASSWORD` wordt via stdin aan `sudo -S` doorgegeven voor de
  package-installatie, OpenVPN-start, OpenVPN-logcontrole en cleanup.
- De Ansible-inventory (`ansible/inventories/<env>/hosts.yml`) leest die
  omgevingsvariabelen voor `ansible_user`, `ansible_password`,
  `ansible_host` en `FORTIGATE_API_TOKEN`.
- De `validate.yml` workflow draait op een pull request en gebruikt
  geen echte secrets en geen VPN; in plaats daarvan gebruikt hij
  dummy waarden zodat syntax- en datavalidatie zonder echte
  apparaattoegang werkt.

## Niet meer gebruikt

De volgende variabelen waren onderdeel van eerdere ontwerpen en zijn
**verwijderd**. Ze mogen niet meer als secret bestaan en mogen ook niet
meer voorkomen in playbooks, workflows of documentatie:

- `ARISTA_SPINE01_HOST`
- `ARISTA_SPINE02_HOST`
- `ARISTA_LEAF01_HOST`
- `ARISTA_LEAF02_HOST`
- `KUBECONFIG`
- `SDN_CONTROLLER_URL`, `SDN_CONTROLLER_TOKEN`
- `ANSIBLE_HOST`, `ANSIBLE_USER`, `ANSIBLE_SSH_PRIVATE_KEY`

## Rotatie

- Wachtwoorden en tokens roteren minimaal volgens het organisatie-
  beleid (bv. elk kwartaal) en altijd na een vermoeden van compromis.
- Na rotatie alleen de waarde in GitHub Secrets bijwerken; de pipeline
  haalt automatisch de nieuwe waarde op bij de volgende run.
