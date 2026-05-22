# Network Automation

End-to-end network automation voor Arista service leafs en FortiGate firewalls,
gestuurd vanaf GitHub via GitHub Actions en uitgevoerd door een self-hosted
runner die tijdens deployment via OpenVPN verbinding maakt met het
beheersegment.

## Architectuur

- **Source of truth**: GitHub. Alle configuratiedata, playbooks en workflows
  staan in deze repository. Wijzigingen lopen via pull requests op `main`.
- **CI/CD**: GitHub Actions. Workflows zijn gedefinieerd in
  `.github/workflows/`.
- **Runner**: `RUNNER01`, een self-hosted GitHub Actions runner met label
  `network-runner`. Alle jobs draaien hierop. RUNNER01 heeft **geen** directe
  netwerktoegang tot het beheersegment en bouwt daarom tijdens de deploy-
  en rollback-jobs eerst een **OpenVPN**-verbinding op.
- **Ansible**: draait op RUNNER01 en stuurt apparaten rechtstreeks aan via
  hun API:
  - `SLEAF01`, `SLEAF02` en `SLEAF03` worden via de Arista eAPI (HTTPS,
    `httpapi` connection) beheerd met de `arista.eos` collection.
  - FortiGate wordt via de FortiGate REST API beheerd met de
    `fortinet.fortios` collection.
- **Batfish**: valideert de gewenste configuratie voor deployment op basis
  van de snapshots in `batfish/snapshots/`.
- **Geen Kubernetes/Cilium**: workloadnetwerken zijn buiten scope.
- **Geen verplichte SDN-controller**: directe API-aansturing is de
  standaard. Een centrale SDN-controller is optioneel en kan later worden
  toegevoegd als policy-orchestration gewenst is.
- **ANSIBLE01**: optioneel. Wordt niet gebruikt in de standaardflow,
  RUNNER01 voert Ansible uit.

## Service leafs

| Host    | Adres        |
|---------|--------------|
| SLEAF01 | 172.19.1.4   |
| SLEAF02 | 172.19.1.5   |
| SLEAF03 | 172.19.1.6   |

De adressen worden via GitHub Secrets (`ARISTA_SLEAF01_HOST`,
`ARISTA_SLEAF02_HOST`, `ARISTA_SLEAF03_HOST`) aan de pipeline doorgegeven.
Wachtwoorden staan **niet** in de repository.

## Benodigde GitHub Secrets

- `VPN_PROFILE`
- `VPN_USERNAME`
- `VPN_PASSWORD`
- `ARISTA_API_USERNAME`
- `ARISTA_API_PASSWORD`
- `ARISTA_SLEAF01_HOST`
- `ARISTA_SLEAF02_HOST`
- `ARISTA_SLEAF03_HOST`
- `FORTIGATE_HOST`
- `FORTIGATE_API_TOKEN`

Concrete waarden voor de service leaf-hosts:

- `ARISTA_SLEAF01_HOST=172.19.1.4`
- `ARISTA_SLEAF02_HOST=172.19.1.5`
- `ARISTA_SLEAF03_HOST=172.19.1.6`
- `ARISTA_API_USERNAME=admin`
- `ARISTA_API_PASSWORD` moet als secret in GitHub worden gezet en mag
  **niet** in Git worden opgeslagen.
- `FORTIGATE_HOST` en `FORTIGATE_API_TOKEN` moeten als secrets worden gezet.

Zie `docs/secrets.md` voor verdere details.

## Environments

De pipeline ondersteunt drie environments: `test`, `acceptance` en
`production`. Per environment is er een inventory in
`ansible/inventories/<env>/hosts.yml` en een group_vars-bestand in
`ansible/group_vars/<env>.yml`. Productiedeploys vereisen handmatige
goedkeuring via de GitHub Environment-protectie.

## Belangrijke Arista-configuratie

- BGP ASN: `65000`
- VLAN-aware bundle: `Main`
- VXLAN interface: `Vxlan1`
- VXLAN source-interface: `Loopback0`
- VXLAN UDP-poort: `4789`

### VLAN-beleid

- **VLAN 1** is de default VLAN en mag **niet** door Ansible beheerd of
  verwijderd worden.
- **VLAN 10 (UWAN_Internet)** is protected en mag **niet** door Ansible
  gewijzigd worden, maar moet wel onderdeel blijven van de
  vlan-aware-bundle `Main`.
- VLANs 2, 3, 4 en 6 worden door Ansible beheerd.

### Een nieuw managed VLAN toevoegen

1. Voeg een entry toe in `ansible/group_vars/<env>.yml` onder
   `datacenter_network.vlans` met `id`, `name`, `vni` en `managed: true`.
2. Voeg het VLAN-id ook toe aan
   `datacenter_network.vlan_aware_bundle.vlans` (zodat Ansible de VXLAN
   mapping op `Vxlan1` en het opnemen in `vlan-aware-bundle Main`
   regelt).
3. Open een pull request naar `main`. De validate-workflow controleert de
   data en Batfish valideert de snapshot. Na merge en goedkeuring rolt de
   deploy-workflow de wijziging uit.

## Workflows

- `.github/workflows/validate.yml` – draait op elke pull request:
  yamllint, ansible-lint, syntax-check, data-validatie. Maakt **geen**
  VPN-verbinding (offline validatie).
- `.github/workflows/deploy.yml` – draait op push naar `main` en via
  `workflow_dispatch`. Voert validatie, Batfish-validatie, opent een
  OpenVPN-verbinding, en maakt een tekstuele change preview. De workflow
  past geen configuratie toe; hij uploadt alleen de wijzigingen die Ansible
  met `--check --diff` zou maken.
- `.github/workflows/rollback.yml` – handmatig via `workflow_dispatch`,
  rolt terug naar een opgegeven git ref. Maakt eerst een OpenVPN-
  verbinding voordat de configuratie wordt teruggezet. Zie
  `docs/rollback.md`.

## Documentatie

- `docs/architecture.md` – architectuur en componenten.
- `docs/environments.md` – test, acceptance, production.
- `docs/secrets.md` – GitHub Secrets en omgevingsvariabelen.
- `docs/rollback.md` – rollback via Git revert en rollback workflow.
- `docs/solid-and-reusability.md` – SOLID-principes en herbruikbaarheid.
- `docs/testplan.md` – testplan en validatiestappen.
