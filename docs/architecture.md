# Architectuur

## Doel

Deze repository automatiseert de configuratie van Arista service leaf
switches en FortiGate firewalls via Ansible, aangestuurd vanaf GitHub
met GitHub Actions. De configuratiedata in `ansible/group_vars/` is de
declaratieve beschrijving van het gewenste netwerk; de pipeline brengt
de echte apparaten in lijn met die data.

## Source of truth en CI/CD

- **GitHub is de source of truth.** Alle configuratiedata, playbooks,
  roles en workflows leven in deze repository. Wijzigingen lopen via
  pull requests op de protected `main`-branch.
- **GitHub Actions stuurt de CI/CD-workflows aan.** Workflows staan in
  `.github/workflows/`:
  - `validate.yml` op pull request
  - `deploy.yml` op push naar `main` en handmatig
  - `rollback.yml` handmatig
- **Runner**: alle jobs draaien op `RUNNER01`, een self-hosted GitHub
  Actions runner met label `network-runner`. RUNNER01 staat **buiten**
  het beheersegment en moet daarom tijdens de deploy- en rollback-jobs
  eerst een OpenVPN-verbinding opbouwen voordat hij de Arista- en
  FortiGate-API's kan bereiken. De validate-workflow is volledig offline
  en heeft geen VPN nodig.

## Uitvoeringslaag

- **Ansible draait standaard op RUNNER01** en gebruikt direct API-
  aansturing (`deployment_mode: direct_device_api`,
  `connectivity: openvpn`).
- **Arista** wordt beheerd via de eAPI over HTTPS met de
  `arista.eos` collection (`ansible_connection: httpapi`).
- **FortiGate** wordt beheerd via de FortiGate REST API met de
  `fortinet.fortios` collection.
- **ANSIBLE01 is optioneel** en wordt niet gebruikt in de standaardflow.
  Indien beschikbaar kan een organisatie kiezen om jobs daarheen te
  forwarden, maar de standaard is RUNNER01.

## Connectiviteit

- RUNNER01 heeft **geen** directe netwerktoegang tot het beheersegment.
- In `deploy.yml` en `rollback.yml` worden via een GitHub Secret
  (`VPN_PROFILE`) en credentials (`VPN_USERNAME`, `VPN_PASSWORD`) een
  OpenVPN-profiel en auth-bestand naar disk geschreven. OpenVPN draait
  in daemon-mode tijdens de job en wordt aan het einde weer opgeruimd.
- `vpn.ovpn`, `vpn-auth.txt` en `vpn.log` zijn opgenomen in
  `.gitignore` zodat ze nooit per ongeluk gecommit worden.

## Validatielaag

- **Batfish** valideert de gewenste configuratie voor deployment op basis
  van de snapshots in `batfish/snapshots/`.
- **Ansible validation role** (`ansible/roles/validation`) controleert de
  declaratieve data: unieke VLAN-id's en namen, protected VLAN-beleid,
  VNI-aanwezigheid, volledigheid van de vlan-aware-bundle, en
  consistentie van firewall-policies.

## Apparaten

Service leafs (echt):

| Host    | Adres        |
|---------|--------------|
| SLEAF01 | 172.19.1.4   |
| SLEAF02 | 172.19.1.5   |
| SLEAF03 | 172.19.1.6   |

De adressen worden via GitHub Secrets aan de pipeline doorgegeven en via
de inventory aan Ansible. Wachtwoorden staan niet in de repository.

## Wat buiten scope is

- **Kubernetes / Cilium** is buiten scope. Workloadnetwerken worden niet
  vanuit deze pipeline beheerd.
- **Aparte SDN-controller** is optioneel. De huidige opzet stuurt Arista
  en FortiGate direct via hun API aan. Indien er later centrale policy-
  orchestration nodig is, kan een SDN-controller worden toegevoegd; dat
  is geen voorwaarde voor de huidige flow.

## VLAN- en VXLAN-beleid

- BGP ASN: 65000
- vlan-aware-bundle: `Main`
- VXLAN interface: `Vxlan1`, source-interface `Loopback0`, UDP-poort 4789
- **VLAN 1** is default en mag niet door Ansible beheerd of verwijderd
  worden.
- **VLAN 10 (UWAN_Internet)** is protected en mag niet door Ansible
  gewijzigd worden, maar moet wel deel uitmaken van
  `vlan-aware-bundle Main`.
- VLANs 2, 3, 4 en 6 worden door Ansible beheerd.

Nieuwe managed VLANs vereisen in alle gevallen:

1. VLAN-database entry op de Arista.
2. VXLAN mapping op `Vxlan1`.
3. Opname in `vlan-aware-bundle Main`.

Deze stappen worden door de `spine_leaf` role automatisch uitgevoerd op
basis van de declaratieve VLAN-lijst.
