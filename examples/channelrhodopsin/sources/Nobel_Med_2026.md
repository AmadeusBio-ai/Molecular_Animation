

*Structural reference: the C1C2 channelrhodopsin dimer, PDB **9GO1**. This is a useful molecular starting point, not a proposed final rendering style.* [RCSB PDB](https://www.rcsb.org/structure/9GO1)

# Best direction: show how light changes molecular connectivity

The **2026 Nobel Prize in Physiology or Medicine** was awarded to **Karl Deisseroth, Peter Hegemann, and Georg Nagel**, “for their discoveries concerning light-gated ion channels and optogenetics.” I accessed the official scientific-background PDF through the Nobel Assembly’s site, since the page you supplied did not load directly. [Nobel Prize in Medicine](https://www.nobelprizemedicine.org/the-nobel-prize-in-physiology-or-medicine-2026/)

For a professional molecular animation, I would build the central sequence around this idea:

> **A small change in retinal reorganizes a protein’s internal interactions, connects an ion-conducting pathway, and ultimately changes a neuron’s electrical activity.**

That causal chain is much more compelling than a glowing protein rotating in space. Channelrhodopsin is particularly suitable because the light sensor and ion-channel function reside in the same protein; the foundational work demonstrated a directly light-gated cation channel, rather than a receptor requiring a separate intracellular signaling cascade. [PubMed](https://pubmed.ncbi.nlm.nih.gov/14615590/)

**My strongest recommendation is a 75–100-second “light-to-current” film, supported by shorter molecular close-ups.** Below are six directions, the specific interactions worth animating, suitable structural assets, and a Blender production approach.

---

# 1. “The twist that opens a pathway”
## Best flagship molecular sequence

**Visual premise:** Start inside an apparently solid membrane protein. A light pulse changes one small chromophore. The camera then follows the consequences through nearby residues until a previously interrupted pathway becomes connected.

### Molecular basis

For this sequence, I would use **C1C2**, an engineered channelrhodopsin chimera, rather than quietly presenting every available structure as native ChR2. C1C2 combines transmembrane helices 1–5 from ChR1 with helices 6–7 from ChR2. Its dimer contains an ion pathway within each protomer—not one central pore between the two proteins. [Nature](https://www.nature.com/articles/s41467-018-06421-9)

The following targets provide a concrete molecular choreography. **Residue numbering here is C1C2 numbering.**

| Molecular target | Evidence to preserve | Proposed animated treatment |
|---|---|---|
| **Retinal–Lys296** | Retinal is covalently attached through a Schiff base; activation involves all-trans → 13-cis isomerization around C13=C14. | Begin with a restrained ball-and-stick close-up. Briefly identify the changing bond, then reveal how its new geometry fits differently into the pocket. |
| **Retinal pocket / Trp262** | Retinal repacking, including the C20 methyl region, accompanies displacement of Trp262. | Let the surrounding aromatic side chains emerge from the protein surface. Keep the movement local; the visual interest comes from changing packing, not a large displacement. |
| **Lys132–Glu129** | The light-activated structure includes an alternative Lys132 conformation interacting with Glu129. | Show a dashed interaction indicator appearing only after the new geometry is established. |
| **Central and inner gates** | Central-gate residues include Ser102, Glu129, and Asn297; the inner bottleneck involves Glu122, His173, and Tyr109. | Reveal these as two successive restrictions along a cutaway pathway. Do not portray all gates as opening simultaneously. |

These selections come from the structural and simulation analysis of Mulder and colleagues. [edoc](https://edoc.hu-berlin.de/bitstreams/869d6236-8e7c-4b5c-a8a7-b7e785fe55d7/download)

### The crucial scientific distinction

**PDB 9GO1 and 9GO2 are not simply “closed” and “fully conducting open.”** The light-activated crystal captures an early, M390-like state. The study reaches a potassium-conducting state through molecular dynamics with altered photocycle protonation assignments. [RCSB PDB](https://www.rcsb.org/structure/9GO1)

That distinction gives the animation a better three-act structure:

**Chromophore changes → early protein rearrangement → conducting-state model.**

Make the transition between experimentally determined coordinates and simulation-derived motion explicit in the production notes or a discreet on-screen label.

### How to make it beautiful

Use a nearly opaque, softly lit protein surface for the opening shot. As the camera approaches the retinal pocket, dissolve only the foreground region into ribbons and selected side chains. Keep the rest of the protein present as a sculptural boundary.

I would use muted blue-green protein, warm amber retinal, and conventional element colors on the handful of chemically important atoms. Reserve brightness for the currently relevant interaction. Avoid turning the entire protein transparent: that usually converts a clear mechanism into overlapping visual noise.

**Signature shot:** the retinal completes its change, the camera pauses, and only then does the surrounding interaction network reorganize. The pause makes the causal relationship readable without exaggerating the molecular displacement.

---

# 2. “Water finds a way”
## Best distinctive, visually sophisticated close-up

**Visual premise:** Make the protein’s *interior space* the protagonist.

A 2018 computational study of ChR2 modeled retinal isomerization and the formation of a water-accessible pathway. Its dark-state model contains an interruption near the retinal-linked **Lys257**, **Glu90**, and **Asn258**. Following activation, water connectivity changes; individual waters move between local sites rather than forming a smooth, macroscopic stream. This was a modeled mechanism, using a ChR2 homology model based on C1C2—not a directly recorded atomic movie. [PNAS](https://www.pnas.org/doi/10.1073/pnas.1700091115)

### Animation idea

Begin with two separated, softly luminous cavity volumes: one accessible from outside the cell, the other from inside. The protein itself is subdued.

At the interruption, introduce a small number of explicit water molecules. The cavities change shape and begin to communicate. Temporary hydrogen-bond indicators appear and disappear as waters reorganize.

For the visual climax, follow one water molecule across the formerly disconnected region, then pull back to reveal the newly connected pathway.

**Important distinction:** water accessibility is not automatically proof of physiologically relevant ion conductance. The film should separate “the pathway hydrates” from “this state supports ion passage.” [PNAS](https://www.pnas.org/doi/10.1073/pnas.1700091115)

### Blender treatment

I would build this with three complementary representations:

- A smooth cavity envelope for overall connectivity.
- Explicit water molecules only near the mechanistic bottleneck.
- Selected side chains defining the cavity boundary.

Use the envelope as an explanatory overlay, not as a literal tube inside the protein. Let it disappear when the camera moves into the atomic close-up.

For hydrogen bonds, use thin, short-lived dashed curves. For water motion, favor irregular translation and rotation with brief local residence—not synchronized beads moving along a spline.

**Signature shot:** the same camera framing before and after activation, with the protein almost unchanged but the internal space now connected. This communicates how a subtle molecular rearrangement can have a large functional consequence.

---

# 3. “One side chain changes the gate”
## Best compact, structurally grounded portfolio film

**Visual premise:** A 20–30-second molecular drama centered on one glutamate side chain.

A particularly useful 2025 study reports high-resolution ground and open structures of the viral channelrhodopsin **OLPVR1**. The central-gate residue **Glu51/E51** changes orientation toward **Asp200/D200**, establishing a hydrogen bond. The corresponding structures are **9IN7**, ground state at 1.1 Å, and **9IN8**, open state at 1.3 Å. [Nature](https://www.nature.com/articles/s41594-025-01488-7)

### Animation choreography

Establish the closed gate in a tight three-quarter view. Keep the starting position of E51 visible as a faint reference silhouette.

Animate the side-chain conformational change with chemically constrained geometry. Reveal D200 as its interaction partner. Only after the endpoint is established should the camera widen to show the changed gate geometry.

Use the experimentally determined endpoints as the anchors; label the interpolated transition as illustrative unless it comes from an appropriate trajectory.

### Why this could look exceptional

A restrained shot can be more impressive than a huge molecular fly-through. The audience sees only a few residues, a confined pocket, and a change in interaction geometry.

I would give the surrounding protein a pale, desaturated material and use saturated color only for E51 and D200. Keep both residues within the depth-of-field plane. Add a ghosted endpoint comparison for perhaps one second, then return to the clean beauty render.

**Boundary:** OLPVR1 is a viral channelrhodopsin, not the original algal ChR2. Present this as a later structural insight into light-gated channels, not as interchangeable footage of the Nobel’s founding molecule. The paper itself treats shared gating principles across subfamilies as an interpretation, not proof that every channel follows an identical atomic path. [Nature](https://www.nature.com/articles/s41594-025-01488-7)

---

# 4. “Light can silence, too”
## Best contrasting mechanism and second molecular scene

**Visual premise:** Repeat the light-triggered opening motif, but reverse the electrical consequence.

The potassium-selective channelrhodopsin **HcKCR1** offers unusually specific choreography. In the 2025 study of its slow-cycling **C110A mutant**, retinal is linked to **Lys233**. Light changes the Schiff-base region’s orientation; **Asp105** movement displaces **Lys84**, while **Asp116** breaks its salt bridge with **Arg244**. These local changes help connect internal cavities in the trimeric assembly. [Nature](https://www.nature.com/articles/s41467-025-56491-9)

### A particularly good ion-following shot

In outward-conducting simulations, potassium interacts successively with:

**Asp116 → Asp229 → Asp105.**

This provides a grounded sequence of temporary coordination sites rather than an arbitrary straight path through the protein. The simulations also retain coordinated water during ion passage. [Nature](https://www.nature.com/articles/s41467-025-56491-9)

Stage this as a handoff of the **ion’s local coordination environment**, not as residues deliberately passing a ball. Show the ion’s irregular movement, transient residence, and changing water contacts.

For the Asp116–Arg244 interaction, a dotted salt-bridge marker can fade as the geometry separates. Keep the side chains solid; do not make the “bond” stretch like an elastic tether.

### Cellular contrast

At the neuron scale, contrast a depolarizing cation-channel response with potassium conductance that can drive inhibition under the appropriate electrochemical conditions. The visual message should be:

> **The effect depends on the channel and ion gradients—not simply on the color of light.** [Nature](https://www.nature.com/articles/s41467-025-56491-9)

Use two matched membrane views with the same camera angle and an accompanying voltage trace. This makes the difference intelligible without adding visual complexity.

The HcKCR1 simulations used high voltages to accelerate rare permeation events, so their event frequency should not be presented as a physiological neuronal rate. [Nature](https://www.nature.com/articles/s41467-025-56491-9)

---

# 5. “From illumination to a causal experiment”
## Best bridge from molecular mechanism to the Nobel’s importance

**Visual premise:** A field of neurons is illuminated, but direct optical activation depends on which cells express the actuator.

The 2005 foundational neuronal study demonstrated genetically targeted, millisecond-timescale optical control. The Nobel background places this within the larger progression from discovering algal light responses to controlling selected neural populations. [PubMed](https://pubmed.ncbi.nlm.nih.gov/16116447/?utm_source=chatgpt.com)

### Animation choreography

Open with a sparse neuronal scene rather than a dense “brain universe.” Use three visually distinguishable categories: actuator-expressing cells, non-expressing neighboring cells, and downstream cells.

A light pulse crosses the scene. At first, show only the directly targeted membrane response. Then reveal the electrical trace and subsequent circuit consequences in a separate visual phase.

The distinction between **direct optical activation** and **downstream recruitment** should remain visible. Otherwise, the animation risks suggesting that every illuminated neuron—or every neuron that later fires—was directly controlled by light.

For the molecular-to-cell transition, cut from the channel’s membrane plane to a larger membrane patch, then to the neuronal surface. I would use matched orientation and color rather than one uninterrupted zoom through many orders of magnitude.

### Avoid the most common visual mistake

Do not make one photon entering one channel instantly produce one whole-neuron action potential. Show a population of channels contributing to a membrane response before depicting a spike. The foundational experiment concerns light-evoked currents and neuronal firing, not a one-photon/one-spike conversion. [PubMed](https://pubmed.ncbi.nlm.nih.gov/16116447/?utm_source=chatgpt.com)

A small, well-timed electrical trace will often explain this better than additional molecular objects.

**Signature shot:** the camera pulls back from many active channels to reveal that their local activity is contributing to one coherent electrical event.

---

# 6. “A second route to sight”
## Best application-focused epilogue

**Visual premise:** Shift from blue-light molecular imagery to an amber retinal projection, linking the molecular switch to a specific human application.

In the 2021 report of partial visual recovery, an optogenetic vector delivered **ChrimsonR** to retinal ganglion cells, combined with light-stimulating goggles. The intervention did not rebuild lost photoreceptors; it provided a different route for light to activate surviving retinal circuitry. The reported recovery was partial and depended on the combined treatment and goggles. [Nature](https://www.nature.com/articles/s41591-021-01351-4?utm_source=chatgpt.com)

### Animation choreography

Show a restrained retinal cross-section with the impaired photoreceptor layer clearly distinguished from the targeted ganglion-cell layer.

Represent the goggles’ output as a simplified pattern of local light pulses. Transition into a ganglion-cell membrane and briefly revisit the light-gated channel motif. Then return to an abstract representation of object detection.

I would **not** show a cinematic blur-to-perfect-vision transformation. Instead, depict a limited object-localization task or an explicitly schematic contrast pattern.

### Molecular asset caution

The available **5ZIH** structure is the crystallized **C1Chrimson construct**, not the exact clinical ChrimsonR–tdTomato fusion. It is useful structural context, but any adaptation into a clinical molecular asset should be documented. [Nature](https://www.nature.com/articles/s41467-018-06421-9)

**Signature shot:** the amber projection pattern and the molecular retinal chromophore briefly share the same visual motif, linking anatomical scale to molecular function without implying that they are the same physical object.

---

# Structural assets worth building around

These are the records I would put into the production asset manifest.

| Asset | Recommended use | Important qualification |
|---|---|---|
| **6EID — native ChR2** | Establishing structure for the founding channel. | Do not pair an unrelated mutant or chimera with it as a simple open-state counterpart. [RCSB PDB](https://www.rcsb.org/structure/6EID?utm_source=chatgpt.com) |
| **9GO1 / 9GO2 — C1C2** | Main chromophore and early-activation sequence. | Dark versus early light-activated structure; full conduction requires additional mechanistic modeling. [RCSB PDB](https://www.rcsb.org/structure/9GO1) |
| **7C86, 7E6Y, 7E6Z, 7E70, 7E71, 7E6X — C1C2** | Time-resolved structural comparison. | Respect chronological ordering and the limits of sparse structural snapshots. [RCSB PDB](https://www.rcsb.org/structure/7C86) |
| **9IN7 / 9IN8 — OLPVR1** | Matched ground/open gate close-up. | Viral channelrhodopsin, not native ChR2. [Nature](https://www.nature.com/articles/s41594-025-01488-7) |
| **9CDC / 9CDD — HcKCR1 C110A** | Potassium-channel gating and coordination sequence. | Dark versus laser-flash-illuminated mutant; use the correct trimeric context. [Nature](https://www.nature.com/articles/s41467-025-56491-9) |
| **5ZIH — C1Chrimson** | Red-shifted-channel structural context. | Not a complete atomic model of the clinical construct. [Nature](https://www.nature.com/articles/s41467-018-06421-9) |

The C1C2 time-resolved series is especially attractive for a restrained structural-comparison film: **dark → 1 µs → 50 µs → 250 µs → 1 ms → 4 ms**. The associated work reports early retinal changes, an outward TM3 shift, and local TM7 deformation. These remain snapshots and interpretations of early events—not a complete experimentally filmed opening trajectory. [eLife](https://elifesciences.org/articles/62389?utm_source=chatgpt.com)

Mulder and colleagues also deposited **MD and quantum-mechanical input/output archives on Zenodo**. Those are worth inspecting before hand-animating a transition. I verified the deposit, but have not downloaded and validated its contents as a Blender-ready trajectory. [Zenodo](https://zenodo.org/records/14245539)

---

# A Blender approach that preserves the science

## Separate molecular coordinates from presentation geometry

Use **Molecular Nodes** as the import and representation layer. Its documented capabilities include PDB/mmCIF import and molecular-dynamics topologies and trajectories, with Blender Geometry Nodes used for visualization. It is not itself a molecular-physics simulator. [Brady Johnston](https://bradyajohnston.github.io/MolecularNodes/?utm_source=chatgpt.com)

I would organize each molecular scene around one coordinate source, feeding separate visual branches for protein surface, ribbons, retinal, selected side chains, waters, ions, and annotations.

This allows the same atoms to drive both the beauty render and the explanatory view. Avoid maintaining independently animated versions of the same molecule.

## Use three clearly distinguished motion categories

**Experimental endpoints:** Align the structures and preserve chain, residue, and atom correspondence. Treat missing atoms, alternative conformations, mutations, and unresolved loops explicitly.

**Simulation-derived trajectories:** Keep the original construct, ion identities, topology, and simulation conditions attached to the shot. Do not relabel a simulated potassium trajectory as sodium because it better fits the narration.

**Illustrative interpolation:** Use constrained, chemically sensible motion between endpoints. Label it as a reconstruction. A smooth transition is not evidence that the molecule followed that exact path.

For production, I would put an evidence field in every shot’s metadata: **experimental / simulation-derived / illustrative**.

## Animate atoms first, then generate surfaces

Keep stable atom identifiers throughout the sequence. Match atoms by chain, residue, and atom name before interpolation.

Avoid directly blending independently remeshed molecular surfaces: their vertex correspondence may differ. Instead, animate the underlying coordinates and generate the surface from that common representation.

For retinal, do not use a generic squash-and-stretch deformation. Preserve the attachment point and chemically plausible bond geometry; the isomerization should read as a specific local transformation.

## Make the membrane a context, not a distraction

Use two leaflet populations with controlled orientation and an exclusion region around the protein. Keep motion subtle in the surrounding membrane, reserving explicit lipid detail for the close-up’s immediate neighborhood.

Before lighting, review the membrane placement in a neutral technical view: extracellular side, intracellular side, hydrophobic belt, and pathway orientation should all be unambiguous.

For the C1C2 dimer, this review is also where I would confirm that the camera is following a protomer’s pathway rather than inventing a pore at the dimer interface. [Nature](https://www.nature.com/articles/s41467-018-06421-9)

## Use sparse, purposeful solvent and ion detail

For an explanatory reconstruction, I would impose stochastic motion, excluded volume, temporary residence near selected sites, and a directional bias appropriate to the stated conditions.

Avoid laminar streams, evenly spaced particles, permanent hydration shells, and perfectly timed “handoffs.” The primary simulations provide better visual precedents: local water-site transitions and intermittent ion coordination. [PNAS](https://www.pnas.org/doi/10.1073/pnas.1700091115)

For C1C2 specifically, the conducting simulations used elevated salt and membrane voltages. Preserve that context in technical documentation rather than presenting their apparent flow rate as normal neuronal physiology. [edoc](https://edoc.hu-berlin.de/bitstreams/869d6236-8e7c-4b5c-a8a7-b7e785fe55d7/download)

## Art direction: prioritize the active interaction

My preferred look would be **soft, sculptural, and selective**, not metallic or heavily emissive.

Keep the protein moderately rough and visually quiet. Give retinal a warm identifying color. Preserve element colors in the chemical close-ups, while using desaturated chain colors for context.

Use broad lighting to describe the protein’s shape and a restrained rim light to separate the cutaway boundary. Keep the important interaction partners in focus together; extreme shallow depth of field can hide the very geometry the audience needs to understand.

I would use three framing modes throughout:

**Surface view** for location and scale; **ribbon-plus-side-chain view** for mechanism; **cavity view** for connectivity.

Transition between those modes deliberately. Do not display all three at equal strength.

## Keep time and scale transitions honest

Retinal photochemistry and subsequent channel activation occupy very different timescales; ultrafast studies distinguish the initial photochemical events from later channel-associated changes. [Nature](https://www.nature.com/articles/s41598-017-07363-w?utm_source=chatgpt.com)

Use changing time labels or explicit transitions rather than one continuous stopwatch. Likewise, use scale bars when moving between atomic, membrane, and cellular views.

A five-second screen-time isomerization can be an effective explanatory choice—as long as the audience is not invited to interpret five seconds as its physical duration.

---

# Suggested 90-second flagship storyboard

*These are editorial timings, not molecular times.*

| Screen time | Shot | Purpose |
|---|---|---|
| **0–10 s** | A selected neuronal membrane receives a light pulse. | Establish the question: how does light change electrical activity? |
| **10–20 s** | Transition into a membrane-embedded channel. | Locate the molecular actuator. |
| **20–33 s** | Surface cutaway reveals retinal and its attachment. | Establish the light-sensitive component. |
| **33–46 s** | Retinal changes; nearby packing and interactions reorganize. | Show a specific causal event. |
| **46–59 s** | Early-state gate geometry becomes visible. | Separate activation from full conduction. |
| **59–72 s** | A labeled conducting-state model reveals connected cavities and sparse ion passage. | Explain functional opening. |
| **72–83 s** | Pull back to a population of channels and an electrical trace. | Connect molecular events to the membrane response. |
| **83–90 s** | Return to the selected neuron and the experimental readout. | Close on controlled biological function. |

This combines the molecular logic of the C1C2 work with the neuronal-control concept established in the foundational experiments, while keeping the difference between those evidence sources visible. [edoc](https://edoc.hu-berlin.de/bitstreams/869d6236-8e7c-4b5c-a8a7-b7e785fe55d7/download)

# What I would build first

I would begin with **one polished 12–15-second retinal-pocket shot**, not the entire neuron scene.

That shot should prove four things: the molecular geometry remains credible, the changing interaction is readable, the surface-to-atomic transition is elegant, and the evidence level is clear.

Then build the cavity-connectivity shot. Those two sequences will determine whether the film feels like a professional scientific explanation or merely attractive molecular scenery.

**The most distinctive visual thesis is this: the protein does not need to become dramatically different in shape for its interior to become functionally different. Make that change visible, and the animation will carry both the beauty and the science.**