"""Storyboard of the channelrhodopsin film, version 4 (pure data, shared by channelrhodopsin_v4.py and
labels_data.py). Version 4 keeps version 3's science, timeline, camera and motion, and changes how the molecules
are drawn and where the film lives:

  - each layer stands for something physical (docs/depiction-sources.md): the protein as cartoons from the
    deposited secondary structure, the residues that act as ball-and-stick in element colours, retinal's
    conjugated chain with its pi lobes (which split at C13=C14 while it twists), the pore as the measured
    free-radius tube, Na+ as cations; only the photons glow (they are light);
  - the camera sees pure white and the film is multiplied onto the website's panel, so it has no frame: the
    membrane is a round patch whose lipids pale toward its rim, and the backdrop no longer turns blue (the blue
    light falls on the molecules instead);
  - the labels are drawn by the web page from labels_data.py, in sync with the clean film; the label pass is
    kept for the downloadable labelled MP4.
"""
FPS, FRAMES, RES = 24, 504, (1920, 1080)

# Stage, as version 3: X right, Y away from the camera, Z up = extracellular; membrane centre at Z = 0.
MEMBRANE_Y = 33.0
YAW_OFFSET = 0.0
SECTION_Y = 2.0
MEMBRANE_RADIUS = 112.0         # a round patch (A) that fits the wide shot, lipids paling over its outer 30 %

T = {
    'photons': (14, 104), 'light': (24, 84), 'cut': (92, 150), 'reveal': (108, 156), 'hero': (154, 176),
    'flash': 176, 'twist': (180, 228), 'ghost': (230, 276), 'network': (262, 318), 'bridge': (306, 326),
    'slab': (356, 400), 'uncut': (392, 420), 'gates': (366, 400), 'cavity': (380, 404), 'open': (410, 436),
}
ION_ENTRIES = (420, 438, 455, 472, 488)
TWIST_STEPS, NETWORK_STEPS = 12, 12

# Motion: version 3's (docs/motion.md; illustrative, from measured rates).
CLOCK_NS, EXPOSURE = 1.0, 2.0
CLOCK_HOLDS = [(T['twist'][0], T['twist'][1], 0.0, 6)]
ANM = {'cutoff': 15.0, 'modes': 30, 'rmsf': 0.8, 'tau': 50.0}
CHI = {'sd': (8.0, 18.0), 'tau': (1.5, 0.3), 'held': (129, 132, 296)}
LIPID = {'head': (0.45, 3.7), 'tail': (0.26, 0.5), 'axial': (1.0, 5.0), 'wobble': (0.17, 1.0),
         'rattle': (1.2, 0.3), 'bob': (1.0, 2.0), 'flow': (4.0, 20.0, 30.0)}
ION_D, ION_EXPOSURE = 133.0, 6.0
ION_RADIUS, ION_MARGIN = 1.35, 0.4
PROTEIN_SCALE = 0.64            # ion clearance is checked against atoms at this x van der Waals (as version 3)
OPEN_RADIUS, CAVITY_MARGIN = 1.3, 0.5
DILATE, DILATE_MAX = 3.8, 3.2
LIPID_SCALE = {'head': 0.62, 'tail': 0.78}

# Residues that act: ball-and-stick. Group 1 = retinal pocket and network, 2 = central/inner gates.
POCKET = {262: 1, 132: 1, 129: 1}
GATES = {102: 2, 297: 2, 122: 2, 173: 2, 109: 2}
SITES = [(140, 'CD'), (136, 'CD'), (129, 'CD'), (122, 'CD')]

CAMERA = [
    (1, 'dimer_top', 330, -28, 14, 50),
    (84, 'dimer_top', 250, -10, 9, 50),
    (160, 'retinal', 44, -2, 5, 50),
    (240, 'retinal', 38, 6, 4, 50),
    (300, 'network', 40, 24, 8, 50),
    (344, 'network', 37, 30, 9, 50),
    (404, ('pore', (-26, -10, 4)), 165, 26, 5, 50),
    (504, ('pore', (-19, -6, 2)), 128, 12, 3, 50),
]
CUT_TARGET = [(1, 'retinal'), (240, 'retinal'), (300, 'network'), (350, 'network'), (392, 'pore')]
APERTURE_RATIO = 0.012

# Look (sRGB 0-255): the website's white page and navy ramp; amber marks retinal's carbons; other atoms of the
# actors in element colours (N blue, O red, S yellow).
AMBIENT_RGB, AMBIENT_STRENGTH = (232, 238, 247), 0.75
PROT_A = ((16, 44, 92), (52, 98, 168))           # protomer A: navy, lighter toward the C-terminus
PROT_B = ((118, 140, 170), (176, 191, 211))      # protomer B: slate
LIPID_HEAD = ((132, 152, 182), (172, 188, 210))   # one step darker than the website plate: the film's membrane
LIPID_TAIL = ((194, 204, 218), (222, 228, 236))   # fills more of the frame, under a brighter key
RETINAL_C = (233, 166, 60)
ELEMENT = {'N': (58, 92, 196), 'O': (206, 68, 60), 'S': (226, 186, 40)}
PI_RGB, PI_EXCITED_RGB = (110, 150, 232), (44, 92, 226)    # excited: deeper, not paler (on white)
ION_RGB = (92, 136, 222)                         # Na+: the positive end of the potential scale, lightened
PHOTON_RGB, CAVITY_RGB, BRIDGE_RGB = (70, 140, 255), (150, 196, 246), (233, 166, 60)
GHOST_RGB = (118, 134, 160)      # the dark-state ghost: darker than the page, so it reads on white
KEY_DIR, KEY_STRENGTH, RIM_DIR, RIM_STRENGTH = (-0.55, -0.8, 0.75), 3.0, (0.35, 0.9, 0.55), 2.0
FILL_DIR, FILL_STRENGTH = (0.7, -0.8, 0.05), 0.9
BLUE_DIR, BLUE_STRENGTH, BLUE_RGB = (0.15, -0.35, 1.0), 2.2, (90, 150, 255)
SAMPLES = 128

# Labels: drawn by the web page (labels_data.py) and, for the downloadable labelled MP4, by the label pass.
LABEL_SCENE, LABEL_PREFIX = 'Channelrhodopsin_v4_Labels', 'CH4L_'
LABELS = {
    'ink': {'dark': (10, 26, 49), 'light': (248, 250, 252)},
    'halo': {'dark': (240, 244, 248), 'light': (2, 15, 38)},
    'shot_ink': [(1, 'dark')],                   # a white picture throughout: dark ink
    'tags_left_from': 378,
    'header': (10, 104, 'NOBEL PRIZE IN PHYSIOLOGY OR MEDICINE 2026  ·  LIGHT-GATED ION CHANNELS'),
    'captions': [  # version 3's wording: the labels state only what records.md supports
        (14, 104, 'Channelrhodopsin C1C2', 'Light-gated cation channel (ChR1/ChR2 chimera) in a membrane'),
        (116, 182, 'Retinal, the light sensor', 'Covalently bound to Lys296 inside each protomer'),
        (190, 256, 'A photon twists retinal', 'All-trans → 13-cis about the C13=C14 bond'),
        (264, 352, 'The protein responds', 'Lys132 swings to Glu129 and forms a salt bridge'),
        (378, 414, 'The pathway is still interrupted', 'In this early light-activated state the gates stay narrow'),
        (424, 504, 'Open channel: cations cross the membrane', 'Conducting state shown as an illustrative model'),
    ],
    'tags': [
        (14, 182, 'X-RAY STRUCTURE  ·  C1C2 DARK STATE  ·  PDB 9GO1'),
        (190, 256, 'ILLUSTRATIVE MORPH  ·  9GO1 → 9GO2'),
        (264, 362, 'X-RAY STRUCTURE  ·  EARLY LIGHT-ACTIVATED STATE  ·  PDB 9GO2'),
        (378, 414, 'PATHWAY FREE-RADIUS PROFILE  ·  PDB 9GO2'),
        (424, 504, 'ILLUSTRATIVE CONDUCTING-STATE MODEL'),
    ],
    'times': [(14, 182, '1 s of film ≈ 1 ns'), (190, 256, 'within a picosecond'), (264, 352, 'microseconds'),
              (378, 414, '1 s of film ≈ 1 ns'), (424, 504, 'milliseconds')],
    'pointers': [
        (30, 104, 'extracellular', 'Extracellular', None),
        (30, 104, 'cytoplasm', 'Cytoplasm', None),
        (44, 104, 'bilayer', 'Lipid bilayer', (150, -70)),
        (122, 182, 'retinal', 'Retinal', (60, -210)),
        (128, 182, 'k296', 'Lys296', (150, 110)),
        (200, 250, 'c13c14', 'C13=C14', (50, -230)),
        (236, 268, 'ghost', 'dark-state position', (-60, -190)),
        (212, 262, 'w262', 'Trp262 shifts', (-110, -170)),
        (296, 352, 'k132', 'Lys132', (150, -100)),
        (296, 352, 'e129', 'Glu129', (160, 90)),
        (376, 414, 'central_gate', 'Central gate', (190, -60)),
        (382, 414, 'inner_gate', 'Inner gate', (190, 60)),
        (434, 470, 'ion', 'Na⁺', (150, -50)),
    ],
}
TAG_LEVELS = ['experimental', 'illustrative', 'experimental', 'experimental', 'illustrative']
