# Full Auto Controls

The `EDITABLE FULL AUTO DEFAULTS` block is natural-language guidance for Qwen.
It is not a hidden command parser. The names and values below are the tested,
recommended vocabulary; equivalent plain-English instructions may also work,
but unknown keys are not guaranteed.

`ENDING MODE` is different: it is a real code-level selector. Its selected
policy is injected into all four Adult Director stages and overrides any
conflicting `ENDING:` line in the editable text.

## Ending Mode

| Selector value | Enforced behavior |
| --- | --- |
| `AUTO` | Chooses a natural ending. A climax is normally optional. Narrow exception: sustained solo manual penile stimulation or a sustained handjob culminates in one visible ejaculation when the duration supports readable buildup. |
| `NO CLIMAX` | Forbids orgasm, ejaculation, cumshot, new climax-related fluid, climax, and climax aftermath. |
| `CLIMAX` | Plans exactly one physically compatible climax after readable buildup. For sustained solo manual penile stimulation or handjob, that climax is one visible ejaculation from the stimulated penis. |
| `LOOP / CONTINUOUS ACTION` | Forbids climax and terminal aftermath, sustains one action, and ends mid-rhythm without a visible reset. |

The selector applies to `ADULT ASSISTED` and `ADULT FULL AUTO`. It has no
effect on `MANUAL` or `STANDARD VISION`.

The manual-stimulation completion rule applies only after direct stimulation
has become the sustained primary action. It does not turn passive exposure,
vague touching, a reach, preparation, or first contact into an ejaculation.
`NO CLIMAX` and `LOOP / CONTINUOUS ACTION` always override this special case.

## Recommended Full Auto vocabulary

| Key | Recommended values or format |
| --- | --- |
| `MODE` | Keep `FULL_AUTO`. |
| `DURATION` | Keep `AUTO — READ FROM LTX DIRECTOR`. The code reads frames and FPS from the LTX Director metadata. |
| `SCENE STYLE` | Short plain-English description. |
| `INTENSITY` | `GENTLE`, `NATURAL`, `PASSIONATE`, or a concise custom description. |
| `ACTION COMMITMENT` | `LOW`, `MEDIUM`, or `HIGH`. |
| `RHYTHM` | Concise plain-English instruction, such as `STEADY`, `CONTROLLED ESCALATION`, or `STRONG CONTROLLED ESCALATION`. |
| `SOFT TISSUE PHYSICS` | `OFF`, `SUBTLE`, or `REALISTIC`. |
| `INERTIA` | `OFF` or `BODY-DRIVEN`. |
| `DAMPING` | `LOW`, `NATURAL`, or `HIGH`. |
| `RESPONSE SCALE` | `SUBTLE`, `MOTION-MATCHED`, or `STRONG`. |
| `OSCILLATION LIMIT` | `NONE` or `SINGLE DAMPED SETTLE`. |
| `CONTACT DEFORMATION` | `ON` or `OFF`. |
| `CONTACT ANCHOR` | `SURFACE-LOCKED` or `FREE`. |
| `VOLUME PRESERVATION` | `ON` or `OFF`. |
| `GRAVITY RESPONSE` | `ON` or `OFF`. |
| `CAMERA` | `PRESERVE` or one explicit camera instruction. |
| `VISIBLE NUDITY AUTO-TRIGGER` | `ON` or `OFF`. |
| `DIALOGUE` | Plain-English instruction or `none unless clearly requested`. |
| `AUDIO` | Plain-English instruction describing permitted sound and music. |
| `PERFORMANCE STYLE` | Recommended: `LIFELIKE AND REACTIVE`. |
| `BODY LANGUAGE` | Recommended: `WEIGHT-AWARE, ASYMMETRIC, CAUSAL`. |
| `FACIAL PERFORMANCE` | Recommended: `CONTEXTUAL MICRO-REACTIONS`. |
| `MOTION TIMING` | Recommended: `ORGANIC, NON-METRONOMIC`. |
| `AUDIO SYNC` | Recommended: `ACTION-BOUND DIEGETIC`. |
| `SUPPORTING MOTION BUDGET` | Recommended: `1-2 RELEVANT CUES PER BEAT`; prevents overloaded choreography. |
| `POSITION RECOGNITION` | Recommended: `AUTO-DETECT FROM VISIBLE GEOMETRY`. |
| `POSITION MODE` | `PRESERVE CURRENT WHEN ACTIVE`, `PRESERVE VISIBLE POSTURES`, or a concise custom request. |
| `POSITION TRANSITION` | Recommended: `MAXIMUM ONE LOW-COST TRANSITION`; use `NONE` for strict pose preservation. |
| `ROLE ASSIGNMENT` | Recommended: `GEOMETRY-BASED, ANATOMY-OWNER LOCKED`. |


## Position and Geometry Intelligence

Adult modes support one to four confirmed adults already visible in the reference image with any visible adult anatomy or presentation. The vision stage does not infer gender identity from anatomy. It assigns stable participants `A` through `D` as needed, records visible anatomy per owner, and detects the current body arrangement from posture, facing direction, relative level, depth, pelvis relationship, support points and exact contact edges.

The system uses broad geometry families rather than depending on a fragile catalogue of named positions. An existing active position is preserved when confidence is sufficient. Ambiguous images retain their visible postures and use only a minimal continuation. Any requested transition is limited to one low-cost, chronological support-and-weight transfer that fits the clip duration.

## Lifelike Prompter behavior

The Lifelike Prompter profile does not simply request more movement. It keeps
one primary action and adds only the body-language, facial, breathing and audio
cues needed to make that action feel intentional and reactive. Weight transfer
precedes effort, reactions follow their trigger, facial performance evolves,
and sustained movement receives slight controlled variation rather than
perfectly repeated cycles.

Every sound should be tied to a visible source and action. Examples include a
footstep at footfall, fabric movement during friction, a furniture creak during
weight transfer, or a breath change after exertion. Detached lists of constant
breathing, vocalization, contact noise and ambience are intentionally avoided.

## Precedence

The Director resolves conflicting instructions in this order:

1. Adult safety and consent gate
2. visible `ENDING MODE` selector
3. explicit assisted request or editable Full Auto settings
4. autonomous scene inference

Do not add a second `ENDING:` instruction to the editable block. Existing old
workflows may still contain `ENDING: AUTO`; v0.1.13 safely overrides it with
the visible selector.


## Mixed Anatomy Continuity

The Full Auto pipeline recognizes a feminine-presenting adult with breasts and a naturally attached visible penis as a valid futanari configuration. It preserves the visible penis instead of normalizing the participant to a vulva-only body. Two or more futanari participants are analyzed independently as A–D as needed, and every anatomy-owner lock is retained through the final prompt.


## Action Intelligence

The autonomous pipeline now classifies the action independently from the body position. It tracks the active effector, source owner, target owner, target surface, contact phase and confidence. Mounted/rider/cowgirl geometry is treated as a position rather than automatically as penetration, while hand-driven and mouth-driven actions remain distinct.

## Duration-Aware Scene Planning

The actual LTX length is detected from the `LTX DIRECTOR — START IMAGE / LENGTH / AUDIO` node. The Prompt Director calculates seconds from source frames and source FPS, then injects a hard duration block into all four Adult stages. A 12-second selection at 24 FPS is therefore recognized as 288 frames / 12 seconds without editing a second field.

Duration creates a nominal beat budget. The Stage-1 scene registry then reduces that budget when participant count, contact count, support instability, occlusion, identity risk or anatomy uncertainty make large changes unsafe. Beats are causal development phases, not automatically new actions. Longer stable clips may add rhythm, range, expression, breathing, grip, weight, body-angle, one compatible secondary action and at most one low-cost transition in that order. Complex scenes use smaller local variations and preserve the established action.

The status field reports detected duration, frame count, FPS, duration source, participant count, anatomy summary, scene complexity and safe beat budget.

## Participant and Anatomy Continuity

Every visible participant is resolved independently before action planning. The generation-control classes are `WOMAN`, `FUTANARI`, `OTHER_ADULT_ANATOMY` and `UNCLEAR`. A feminine-presenting adult with a naturally attached visible or compatible partially visible penis is retained as FUTANARI; feminine presentation never removes the penis. A confirmed vulva may coexist and is locked separately. Covered or ambiguous anatomy remains UNCLEAR rather than being guessed.

Up to four visible adults may be registered, but no more than one primary and one compatible secondary action are activated. Other participants retain their identity, anatomy, pose, support and existing contacts with only conservative local reactions.

## Primary Action Resource Protection

- Every participant-owned penis is tracked independently as a resource.
- Anatomy used by the established primary penetrative action is marked `ENGAGED_PRIMARY`.
- `ENGAGED_PRIMARY` anatomy cannot become a handjob, self-manual, oral or alternate-action target.
- A new manual penis secondary requires both a free reachable hand and a separate target listed as `FREE_VISIBLE`.
- If no separate free target exists, the primary action continues with rhythm, balance, expression and non-conflicting support variations.


## Visibility and Occlusion Continuity

- Anatomy existence is tracked independently from current visibility.
- A confirmed futanari penis remains `PRESENT_LOCKED` through body overlap, camera cropping, anal/vaginal receiving roles and temporary occlusion.
- `OCCLUDED` never becomes `ABSENT`, smooth anatomy or a woman-only reinterpretation.
- Each hand is locked by owner and side with separate palm, finger, digit-count and wrist/forearm evidence.
- Partial or occluded hands use `PRESERVE_OCCLUSION_NO_COMPLETION`; hidden fingers stay hidden and cannot become a sixth digit or duplicated thumb.
- These safeguards affect planning and validation while the high-detail render profile remains unchanged.


## High-Detail Native Output

The final path preserves the full Stage-2 decoded dimensions. The former 0.75 downscale and x3 bicubic prescale are disabled. The accepted high-detail profile uses Stage 2 at 4 steps with a 0.40 sigma endpoint. Optional RTX VSR remains disabled by default and is prepared as a clean source-ratio x2 pass without Denoise or Deblur.
