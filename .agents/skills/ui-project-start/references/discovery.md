# Discovery and Existing UI Authority

## Authority classification

- `approved`: explicitly approved with recorded scope
- `functional-only`: preserve behavior, data, routing, accessibility, and performance, but not visual precedent
- `experimental`: an unvalidated candidate or limited experiment
- `deprecated`: explicitly rejected or replaced

Starter templates, generative-AI drafts, hackathon screens, and programmer art are `functional-only` unless explicit evidence says otherwise.

## Investigation order

1. user requirements, product documents, and core flows
2. actual data model and content shapes
3. runnable screens and key states
4. design tokens, components, theme, brand, and world assets
5. tests, Storybook, screenshots, Figma, and approval records
6. platform, input, accessibility, performance, and fairness constraints
7. how the existing UI was created

## Separate function from appearance

| May preserve | Do not preserve automatically |
| --- | --- |
| data and domain rules | screen division and layout |
| routes and permissions | sidebars, tabs, and card choices |
| validation rules | field placement and visual hierarchy |
| game events and state | HUD position and decoration |
| accessibility and performance constraints | color, typography, and component composition |
| tested behavior | temporary design tokens |

## Content investigation

- minimum, typical, and maximum item counts
- short and long names and translations
- image availability and aspect ratios
- numbers, units, currency, dates, and statuses
- real-time change and freshness
- permission, lock, and partial-data conditions
- empty data and errors

Do not validate layout only with `Lorem ipsum`, identical title lengths, and perfect images.
