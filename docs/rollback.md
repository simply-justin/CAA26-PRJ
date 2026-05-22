# Rollback

GitHub is de source of truth, dus de standaardmanier om wijzigingen
terug te draaien is via Git. Daarnaast bestaat er een dedicated
rollback-workflow voor het snel terugrollen van een specifieke
environment naar een eerdere ref.

## Optie 1: Git revert

1. Identificeer de commit(s) op `main` die teruggedraaid moeten worden.
2. Maak een `git revert <sha>` (of meerdere) in een nieuwe branch.
3. Open een pull request naar `main`. De `validate.yml` workflow draait.
4. Na merge draait `deploy.yml` automatisch en brengt de apparaten
   terug naar de eerdere gewenste staat (inclusief het opzetten van de
   OpenVPN-verbinding richting het beheersegment).

Deze route is geschikt voor "platte" rollbacks waarbij de revert zelf
de gewenste configuratie wordt.

## Optie 2: Rollback workflow

De workflow `.github/workflows/rollback.yml` voert een gerichte rollback
uit zonder dat de `main`-historie aangepast hoeft te worden.

Inputs:

- `environment`: `test`, `acceptance` of `production`
- `ref`: een git tag, branch of commit SHA (bv. `stable-production-v1`)
- `reason`: vrije tekst, verplicht voor auditing

Werking:

1. Checkout van de gekozen ref.
2. Syntax check en data-validatie (`ansible/playbooks/validate.yml`).
3. Opzetten van de OpenVPN-verbinding via `VPN_PROFILE`,
   `VPN_USERNAME` en `VPN_PASSWORD`.
4. Dry-run met `--check --diff`.
5. Apply: `ansible/playbooks/deploy.yml` brengt de apparaten in lijn met
   de configuratie van die ref.
6. Verify: `ansible/playbooks/verify.yml` controleert dat VLANs, VXLAN-
   mappings en `vlan-aware-bundle Main` op Arista aanwezig zijn, en
   dat FortiGate-objecten opvraagbaar zijn.
7. Cleanup van OpenVPN en credential-bestanden (`if: always()`).

De rollback workflow vereist - net als `deploy.yml` voor `production` -
een handmatige goedkeuring via de GitHub Environment-protectie.

## Aanbevolen praktijk

- Tag stabiele productiestates expliciet (bv. `stable-production-vN`).
- Voer na elke rollback een `git revert` of forward-fix uit, zodat
  `main` weer overeenkomt met de werkelijk uitgerolde state.
- VLAN 1 en VLAN 10 (UWAN_Internet) zijn protected: ook bij rollbacks
  zal de validatie weigeren wanneer een ref deze VLANs als `managed`
  markeert of VLAN 10 uit `vlan-aware-bundle Main` haalt.
