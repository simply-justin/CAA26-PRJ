# Environments

De pipeline ondersteunt drie environments. Er is **geen** `poc`
environment.

| Environment   | Doel                                              | Goedkeuring        |
|---------------|---------------------------------------------------|--------------------|
| `test`        | Eerste test van wijzigingen op testapparatuur     | Automatisch        |
| `acceptance`  | Acceptatie en validatie tegen productieachtige    | Reviewer in PR     |
|               | configuratie                                      |                    |
| `production`  | Echte service leafs en FortiGate                  | Handmatige approval |

## Datastructuur per environment

- `ansible/inventories/<env>/hosts.yml` – inventory met de actuele
  apparaten en API-credentials uit environment variables.
- `ansible/group_vars/<env>.yml` – environment-specifieke
  configuratiedata. Per environment alleen `environment_name`
  afwijkend; alle netwerk- en securityvariabelen zijn identiek tenzij
  expliciet aangepast.
- `ansible/group_vars/all.yml` – platformbrede variabelen (GitHub als
  source of truth, RUNNER01 als runner, direct device API als
  deployment mode, OpenVPN als connectivity).

## Workflow selectie

- `validate.yml` (pull request): forceert `TARGET_ENV=test` met dummy
  hosts/credentials zodat syntax- en datavalidaties zonder echte
  apparaattoegang draaien. Maakt **geen** VPN-verbinding.
- `deploy.yml` (push naar `main` of handmatig): standaard `test`,
  via `workflow_dispatch` kan een reviewer `acceptance` of
  `production` kiezen. Bouwt eerst een OpenVPN-verbinding op en sluit
  die aan het einde van de job weer af.
- `rollback.yml` (handmatig): vereist environment, git ref en reden.
  Bouwt ook eerst een OpenVPN-verbinding op.

## Productie-beveiliging

- `main` is een protected branch.
- De `production` environment in GitHub vereist handmatige approval.
- Secrets zijn gescheiden per environment waar dat zin heeft.
- OpenVPN-credentials (`VPN_PROFILE`, `VPN_USERNAME`, `VPN_PASSWORD`)
  zijn alleen beschikbaar in de deploy- en rollback-jobs.
