---
version: alpha
name: Central de Inteligência Tributária e Auditoria
description: Dashboard analítico local para leitura agregada de finanças públicas de Palmas/TO.
colors:
  primary: "#C5E86C"
  background: "#101210"
  surface: "#171A17"
  surfaceRaised: "#1D211D"
  border: "#303630"
  text: "#F1F3ED"
  mutedText: "#B3B9B0"
  subtleText: "#818A80"
  positive: "#8DCC79"
  negative: "#E88278"
  realData: "#93B8D5"
  syntheticData: "#E1BD70"
  estimatedData: "#B8A2E2"
typography:
  sans:
    fontFamily: '"Inter", "Segoe UI", system-ui, -apple-system, Arial, sans-serif'
rounded:
  sm: "8px"
  md: "9px"
  lg: "13px"
spacing:
  sidebar-width: "252px"
  page-inline: "34px"
  panel-gap: "17px"
components:
  navigation: { style: "fixed charcoal sidebar; lime selected marker; wraps above 950px" }
  card: { style: "dark tonal panel, 1px border, 13px radius, restrained shadow" }
  metric: { style: "tabular figures, lime left rule, label and provenance detail" }
  chart: { style: "transparent plot over dark panel, lime primary series, subdued grid" }
  filter: { style: "dark authored Dash dropdown with visible lime focus" }
  status: { style: "persistent inline notice; distinguish source, estimate, synthetic and errors" }
---

# Central de Inteligência Tributária — Design System

## Overview

### Creative North Star

An operational fiscal observatory: the restrained density of a public-sector briefing, with the visual discipline of a dark instrument panel. The existing Dash shell and Visão Executiva are the canonical examples. New pages extend that visual world; they do not introduce a second brand.

### Product context and register

- **Audience and primary job:** analysts and public managers reviewing aggregated fiscal indicators, data provenance, and governance limits.
- **Target market(s) and evidence:** Palmas, Tocantins, Brazil; repository documentation and UI copy identify the municipality.
- **Locale(s) and language policy:** Brazilian Portuguese; currency uses BRL formatting and dates are displayed in Brazilian order when rendered as text.
- **Usage scene:** desktop-first analytical workspace with responsive tablet and narrow-screen navigation.
- **Register:** product / operate and read; read-only analytics.
- **Memorable signature:** lime focus line and compact source/status badges.
- **Restraint:** preserve readable charts, explicit methods and limitations; avoid decorative motion and unsupported claims.
- **Anti-references:** neon trading terminals, bright generic Bootstrap dashboards, glassmorphism, and dashboards that imply forecasts or individual risk scores.
- **Token ownership/runtime mapping:** `dash_app/assets/style.css` is the runtime token source; `dash_app/assets/exec.css` and `dash_app/components/` consume its CSS variables. This file documents the existing values, not a parallel token generator.

## Colors

Charcoal background `#101210`, layered surfaces `#171A17` / `#1D211D`, borders `#303630`, off-white text `#F1F3ED`, and muted text `#B3B9B0` / `#818A80`. Lime `#C5E86C` marks the main series, selected navigation, and keyboard focus. Positive/negative indicators use `#8DCC79` / `#E88278`. Blue, amber, and lavender provenance colors identify recorded, synthetic, and estimated data; they are never used as unqualified performance signals. Charts inherit this palette and use transparent backgrounds.

## Typography

Inter leads the stack, followed by Segoe UI and system sans fallbacks. Headings are compact and medium-bold. Body copy is short, muted, and comfortably spaced. Numeric values use tabular alignment where possible. Keep Portuguese labels natural; avoid all-caps except small navigation/eyebrow metadata.

## Layout

The desktop shell has a 252px fixed sidebar and a centered content region up to 1450px. Panels use about 17px vertical rhythm, internal padding around 17–25px, and responsive grids. At 950px navigation moves above content; at 620px metrics and filters stack. Data panels remain readable without horizontal page overflow.

## Elevation & Shapes

Hierarchy comes from small tonal shifts, thin borders, and a restrained shadow. Panels use 13px corners; controls use 8–9px. Avoid blur and heavy gradients. Lime focus outlines remain visible against dark surfaces.

## Components and states

- Navigation, panels, KPIs, badges, charts, filters, and status notices use shared CSS and Python primitives in `dash_app/components/`.
- Every data surface distinguishes ready, empty, unavailable, and error states. Missing local sources display an explanation and do not fabricate figures.
- Charts use Plotly transitions around 240ms, while `prefers-reduced-motion: reduce` disables CSS transitions and entrance motion.
- All interface data is aggregated. No page displays names, taxpayer identifiers, contract descriptions, or individual debt records.
- Alerts are triage signals, not findings of irregularity. Estimated geographic measures and synthetic model outputs are labeled and constrained in context.

## Content and visualization

Use direct Brazilian Portuguese, identify the selected period, preserve negative expense movements, and explain whether sums are nominal, preliminary, estimated, or incomplete. A chart is not evidence of official reconciliation. Tooltips supplement visible labels and never carry essential limitations alone.

## Do's and Don'ts

- **Do:** show provenance and caveats beside the figures they qualify.
- **Do:** use the lime accent for one primary series or interaction at a time.
- **Don't:** suggest that a model predicts real delinquency or can authorize collection.
- **Don't:** infer individual eligibility or prioritize individuals using territorial aggregates.
