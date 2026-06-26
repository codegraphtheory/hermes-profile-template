---
name: Profile improvement
description: Suggest an improvement to the Hermes profile template
title: "Profile improvement: "
labels: [enhancement]
body:
  - type: textarea
    id: use_case
    attributes:
      label: Use case
      description: What profile authoring problem should this solve?
    validations:
      required: true
  - type: textarea
    id: proposal
    attributes:
      label: Proposal
      description: What should change?
    validations:
      required: true
  - type: textarea
    id: risks
    attributes:
      label: Risks
      description: Any safety, compatibility, or maintenance risks?
---
