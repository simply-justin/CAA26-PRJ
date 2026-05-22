# SOLID en herbruikbaarheid

De repository volgt expliciet SOLID-principes en herbruikbaarheid om
configuratiedata, validatie en uitvoering gescheiden te houden. Dit
houdt de pipeline begrijpelijk, testbaar en uitbreidbaar zonder
duplicatie tussen environments.

## Scheiding van configuratiedata en uitvoeringslogica

- **Configuratiedata** leeft in `ansible/group_vars/`:
  - `all.yml`: platformbrede variabelen (GitHub, RUNNER01, direct
    device API, OpenVPN als connectivity).
  - `test.yml`, `acceptance.yml`, `production.yml`: per environment.
    Alleen `environment_name` verschilt standaard; de overige structuur
    is identiek zodat een wijziging in `test` direct overdraagbaar is
    naar `acceptance` en `production`.
- **Uitvoeringslogica** leeft in `ansible/playbooks/` en
  `ansible/roles/`:
  - `playbooks/validate.yml` – pure datavalidatie op `localhost`.
  - `playbooks/deploy.yml` – orchestreert validatie + apparaatconfiguratie.
  - `playbooks/verify.yml` – post-deployment verificatie.
  - `roles/validation` – generieke datavalidatie van VLANs, VXLAN,
    vlan-aware-bundle, en firewall-policies.
  - `roles/spine_leaf` – generieke Arista-configuratie op basis van
    `datacenter_network.vlans` en `vlan_aware_bundle`.
  - `roles/fortigate` – generieke FortiGate-configuratie op basis van
    `network_security_stack`.
- **Connectiviteit** (OpenVPN) is een platformverantwoordelijkheid van
  de workflow, niet van Ansible. De roles weten niet hoe RUNNER01 het
  beheersegment bereikt; ze gebruiken alleen `ansible_host` en
  API-credentials.

Geen enkele role kent een specifieke VLAN of policy "by name"; alles
loopt via de declaratieve lijst in `group_vars`. Daardoor schaalt de
oplossing: een extra VLAN of zone is een data-wijziging, geen code-
wijziging.

## SOLID-toepassing

- **Single Responsibility**: elke role doet exact één ding -
  validatie, Arista of FortiGate. Playbooks zijn dunne orchestrators.
  De VPN-opbouw is een aparte verantwoordelijkheid van de workflow.
- **Open/Closed**: nieuwe VLANs, zones of policies worden toegevoegd
  door data uit te breiden, niet door bestaande tasks te wijzigen.
- **Liskov-substitutie**: alle environments gebruiken dezelfde
  playbooks en roles; alleen de inventory en group_vars wisselen. Een
  environment kan een andere zonder code-aanpassingen "vervangen".
- **Interface segregation**: de inventory expose't alleen wat een
  groep nodig heeft. `arista`-hosts krijgen `arista.eos.eos` als
  network_os, `fortigate`-hosts krijgen `fortinet.fortios.fortios`.
- **Dependency Inversion**: playbooks en roles hangen af van
  abstracties (variabelen onder `datacenter_network` en
  `network_security_stack`), niet van concrete hostnamen of adressen.
  Hostadressen en credentials komen via environment variables uit
  GitHub Secrets. De OpenVPN-verbinding wordt door de workflow
  ge\u00efnjecteerd; Ansible hoeft niet te weten dat er een tunnel onder
  ligt.

## Herbruikbaarheid

- Eén set roles voor alle environments.
- Eén set playbooks voor `validate`, `deploy` en `verify`.
- Eén workflow per fase (`validate`, `deploy`, `rollback`). De VPN-
  stappen in `deploy.yml` en `rollback.yml` zijn identiek opgebouwd.
- Geen aparte domeinmappen of duplicate configuratiemappen. De Ansible
  `group_vars` is de centrale configuratiedata.
- Protected VLAN-beleid (VLAN 1 default, VLAN 10 UWAN_Internet) is
  data-gedreven via `datacenter_network.protected_vlans` en wordt door
  zowel de validation role als de spine_leaf role gerespecteerd.
