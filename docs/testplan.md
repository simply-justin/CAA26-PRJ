# Testplan

Dit testplan beschrijft welke checks de pipeline uitvoert en hoe je ze
lokaal reproduceert.

## Lokale checks

Voer vanuit de repository root uit:

```bash
yamllint ansible/ .github/workflows/ batfish/
ansible-lint ansible/playbooks/ ansible/roles/

ansible-playbook ansible/playbooks/validate.yml \
  -i ansible/inventories/test/hosts.yml \
  -e target_environment=test \
  --syntax-check

ansible-playbook ansible/playbooks/deploy.yml \
  -i ansible/inventories/test/hosts.yml \
  -e target_environment=test \
  --syntax-check

ansible-playbook ansible/playbooks/verify.yml \
  -i ansible/inventories/test/hosts.yml \
  -e target_environment=test \
  --syntax-check

ansible-playbook ansible/playbooks/validate.yml \
  -i ansible/inventories/test/hosts.yml \
  -e target_environment=test
```

De laatste run draait de validation role op `localhost` en vereist
geen netwerktoegang en geen VPN.

## Pull request (validate workflow)

`.github/workflows/validate.yml` draait op iedere PR naar `main` en
voert uit (zonder VPN):

1. Checkout
2. Install Python + Ansible collections
3. `yamllint` op `ansible/`, `.github/workflows/`, `batfish/`
4. `ansible-lint` op `ansible/playbooks/` en `ansible/roles/`
5. `--syntax-check` op alle playbooks
6. Ansible data-validatie via de validation role (geen apparaattoegang
   nodig; gebruikt dummy hostadressen via env vars)

## Push naar main (deploy workflow)

`.github/workflows/deploy.yml` voert in volgorde uit:

1. `validate` job (zoals hierboven, maar met echte secrets als env vars).
2. `batfish` job:
   - Start `batfish/allinone` container.
   - Initieert snapshot uit `batfish/snapshots/test/`.
   - Runt `batfish/validate.py`, dat controleert dat de drie service
     leafs (`sleaf01`, `sleaf02`, `sleaf03`) in de snapshot aanwezig zijn.
3. `deploy` job:
   - Installeert `openvpn`, `iproute2`, `iputils-ping`, `curl`.
   - Schrijft `vpn.ovpn` en `vpn-auth.txt` (mode 600) op basis van
     `VPN_PROFILE`, `VPN_USERNAME`, `VPN_PASSWORD`.
   - Start OpenVPN in daemon-mode en wacht 20 seconden op routes.
   - Controleert API-bereikbaarheid naar de Arista-leafs en de FortiGate.
   - Maakt een tekstuele change preview met `--check --diff` en uploadt
     die als workflow-artifact (`<environment>-deployment-preview`).
   - Past geen configuratie toe; de workflow logt alleen welke wijzigingen
     Ansible zou maken.
   - Cleanup-stap (`if: always()`) sluit OpenVPN en verwijdert de
     credential-bestanden.

Voor `production` is een GitHub Environment-approval geconfigureerd.

## Verify-stap

`ansible/playbooks/verify.yml` controleert per service leaf:

- Alle managed VLANs verschijnen in `show vlan brief`.
- Voor elke managed VLAN bestaat de juiste VXLAN VNI-mapping op
  `interface Vxlan1`.
- `vlan-aware-bundle Main` is aanwezig in de BGP-configuratie.

En op de FortiGate:

- Address-objects zijn opvraagbaar via de REST API.

## Rollback

Zie `docs/rollback.md`. De rollback-workflow draait dezelfde validate-,
syntax-check-, VPN-opbouw-, dry-run-, apply-, verify- en cleanup-
stappen, maar op een gekozen git ref.

## Wat niet wordt getest in deze pipeline

- Kubernetes/Cilium netwerk (buiten scope).
- Aparte SDN-controller (optioneel, niet ingeschakeld).
