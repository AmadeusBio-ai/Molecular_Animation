"""Storyboard of the ART film, version 3 (pure data, read by art_rna_v3.py). Version 3 keeps version 2's science,
placements, timeline, camera and motion (the same random streams, so the same tumbling and the same RT close-up),
and changes how the molecules are drawn and where the film lives:

  DNA        atom by atom, as the website's DNA plates draw it: a stick for every covalent bond (the stacked
             templates' O3'-P links closed to 1.6 A, art_locus.close_backbone), the sugar and base rings filled
             as plates, each phosphate group (one negative charge) as red balls. As the camera pulls back until a
             bond is smaller than a pixel, the same atoms swell to space-filling (groups.ball_stick, Detail).
             The repeat copies light in the website's amber, by colour only.
  RNAs       atom by atom too (thicker sticks for their distance), teal, translucent where pLDDT is low; they
             resolve atom by atom as in version 2.
  RT         a cartoon, secondary structure estimated from the predicted Calpha positions (molanim.cartoon),
             coloured by confidence: pLDDT >= 90 navy, 70-90 steel, below 70 pale and translucent. YADD in
             ball-and-stick, amber carbons.
  Partner    a translucent coral cartoon (mean pLDDT 33), fading in.
  Ground     pure white, no glow: the film is multiplied onto the website's panel, so it has no frame. The
             labels, locus map and AlphaFold notice are drawn by the web page from labels.json (and by the label
             pass for the downloadable labelled film).
"""
FPS, FRAMES, RES = 24, 744, (1920, 1080)
SAMPLES = 96

# Stage and placements: version 2's.
GENOME = (9421, 10900)
CENTRE_BP = 9972
DNA_WAYPOINTS = [(0, 0, 0), (700, 90, 50), (1400, -40, -40), (2100, 70, 30), (2800, -60, -30), (3500, 40, 40),
                 (4200, -30, -20), (4900, 20, 10), (5600, 0, 0)]
RNA_PLACE = {'W1': ((0, -200, -200), (14, -10)), 'W2': ((0, -90, -175), (-20, 25)),
             'W3': ((0, -260, -165), (35, 8)), 'W4': ((60, -140, -150), (-8, -20))}
RT_PLACE = ((-40, -200, -195), 10376)
PARTNER_OFFSET = (175.0, 30.0, 95.0)

LIT = [46, 100, 124, 144, 162]
T = {
    'diagram': (196, 258), 'rna': [266, 284, 302, 320], 'rt_in': 300, 'cut': (474, 516), 'yadd': (496, 528),
    'uncut': (566, 600), 'partner': (586, 628), 'follow': (440, 490, 590, 640),
    'detail': (104, 150),               # the DNA goes from atom by atom (1) to space-filling (0) during the pull-back
}

# Motion: version 2's (docs/motion.md).
CLOCK_NS, EXPOSURE, SHUTTER, TEMP = 5.0, 16.0, 'triangle', 310.15
SHUTTER_ARGS = {'substeps': int(4 * EXPOSURE), 'shutter': SHUTTER}
CROWDING = {'translation': 4.0, 'rotation': 2.0}
TETHER = {'shift': 9.0, 'turn': 0.35}
RT_SEED = 339
ANM = {'rt': (15.0, 24, 1.0, 50.0), 'partner': (15.0, 24, 2.0, 30.0), 'rna': (20.0, 24, 2.5, 60.0)}
CHI = {'sd': (8.0, 18.0), 'tau': (1.5, 0.3)}
DNA_MOTION = {'persistence': 500.0, 'twist_persistence': 750.0, 'waves': (150.0, 300.0, 600.0), 'twist_length': 200.0,
              'friction': 2.0}
APERTURE_RATIO = 0.012

CAMERA = [
    (1, ('dna_start', (0, 0, -4)), 165, -36, 12, 50),
    (72, ('rep1', (0, 0, -4)), 420, -24, 10, 50),
    (190, ('array', (0, 0, -120)), 5400, -6, 8, 50),
    (252, ('array', (0, 0, -130)), 5150, -3, 8, 50),
    (344, ('w23', (0, 0, -40)), 1300, -4, 6, 50),
    (424, 'w4', 1000, 6, 6, 50),
    (494, 'yadd', 235, 0, 6, 50),
    (566, 'yadd', 215, 7, 6, 50),
    (648, 'tableau', 960, 8, 4, 50),
    (744, 'tableau', 900, 11, 5, 50),
]

# Look (sRGB 0-255): the website's white page and its plates' palette.
AMBIENT_RGB, AMBIENT_STRENGTH = (232, 238, 247), 0.75
KEY = ((-0.55, -0.8, 0.75), 3.0, (255, 247, 238))
FILL = ((0.7, -0.8, 0.05), 0.9, (226, 236, 255))
RIM = ((0.35, 0.9, 0.55), 2.0, (255, 255, 255))
NAVY = ((16, 44, 92), (52, 98, 168))
STEEL = ((51, 81, 119), (122, 148, 184))
DNA_STRANDS = (NAVY, STEEL)                          # as the website's DNA plate
DNA_BASE = (176, 190, 212)                           # a step deeper than the plate: many bases overlap here
PHOSPHATE = (192, 62, 56)                            # one negative charge, in the potential scale's red
LIT_STRAND, LIT_BASE, LIT_PHOSPHATE = ((226, 150, 44), (238, 182, 96)), (246, 214, 160), (222, 136, 36)
ELEMENT = {'N': (58, 92, 196), 'O': (206, 68, 60), 'S': (226, 186, 40)}
DNA_STICK = 0.28                                     # A: the plate's 0.2 read thin at the opening's 165 A
BALL = {'P': 2.6, 'OP1': 1.9, 'OP2': 1.9}            # phosphate balls, in stick radii; other atoms are joints
PLATE_OPACITY = {'dna': (0.75, 0.92), 'rna': (0.5, 0.8)}   # ring plates: facing / silhouette
FILL_SCALE = 0.70                                    # space-filling at 0.70 x van der Waals (version 2)
RNA_STICK = 0.42                                     # seen from 1,000-1,300 A: about two pixels
RNA_TEAL = ((10, 112, 120), (64, 176, 176))
RNA_PALE = (150, 206, 206)
RNA_ALPHA = (0.45, 0.9)                              # opacity at low / high pLDDT
RT_BANDS = {90: (30, 62, 120), 70: (96, 128, 172), 0: (176, 192, 214)}
RT_ALPHA = {90: 1.0, 70: 1.0, 0: 0.4}
PARTNER = (214, 112, 96)
PARTNER_ALPHA = (0.35, 0.6)
AMBER = (233, 166, 60)

# Labels: version 2's, drawn by the web page (labels.json) and by the label pass for the labelled film.
LABEL_SCENE, LABEL_PREFIX = 'ArtRna_v3_Labels', 'AR3L_'
INK = {'dark': (10, 26, 49), 'light': (248, 250, 252)}
LABELS = {
    'ink': INK,
    'halo': {'dark': (240, 244, 248), 'light': (2, 15, 38)},
    'shot_ink': [(1, 'dark')],
    'header': (10, 258, 'ART  ·  ARRAY-ASSOCIATED REVERSE TRANSCRIPTASE  ·  STAPHYLOCOCCUS PHAGE SA1'),
    'captions': [
        (12, 168, 'A rhythm in a phage genome', 'A repeat recurs between unique spacers in the DNA of phage SA1'),
        (178, 258, 'A repeat array beside a reverse transcriptase gene',
         'The layout resembles a CRISPR array, but ART loci lack cas genes'),
        (268, 424, 'The array is expressed as distinct short RNAs',
         'Up to 8 % of phage RNA 15 min into infection; the shapes shown are uncertain predictions'),
        (436, 590, 'Beside it, a reverse transcriptase',
         'Its family copies RNA into DNA; whether this one is active is untested'),
        (602, 744, 'The components are emerging', 'Their molecular relationship remains to be resolved'),
    ],
    'tags': [
        (12, 258, 'SEQUENCE  ·  GENBANK MW218148.1  ·  DNA SHAPE ILLUSTRATIVE'),
        (268, 424, 'ALPHAFOLD 3 PREDICTIONS  ·  RNA ENDS ASSUMED'),
        (436, 590, 'ALPHAFOLD 3 PREDICTION  ·  RT QPI16926'),
        (602, 744, 'HYPOTHESES  ·  NO CONFIDENT INTERFACE PREDICTED'),
    ],
    'times': [
        (12, 258, 'Repeat positions: our comparison of the sequence'),
        (268, 424, 'Low confidence  ·  mean pLDDT 40–50'),
        (436, 590, 'pTM 0.80  ·  translucent: pLDDT below 70'),
        (602, 744, 'Partner mean pLDDT 33  ·  complexes ipTM ≤ 0.24'),
    ],
    'pointers': [
        (50, 128, 'rep1', 'Repeat', (150, -120)),
        (104, 150, 'spacer1', 'Spacer', (110, 110)),
        (282, 424, 'W1', 'Unit 1', (-70, 140)),
        (300, 424, 'W2', 'Unit 2', (-70, 140)),
        (318, 424, 'W3', 'Unit 3', (-70, 140)),
        (336, 424, 'W4', 'Unit 4', (-70, 140)),
        (504, 590, 'yadd', 'YADD motif', (270, -170)),
        (626, 744, 'rt', 'Reverse transcriptase', (-150, -190)),
        (640, 744, 'partner', 'Partner protein', (-70, -170)),
        (652, 744, 'W4', 'Array RNA', (-60, -160)),
    ],
    'links': [],                        # filled in build(): guides and hypotheses
}
TAG_LEVELS = ['experimental', 'predicted', 'predicted', 'symbolic']
DIAGRAM = {'y': 832, 'x': (300, 1620), 'span': (9421, 12951), 'h': (24, 14), 'scale_bp': 500}
DIAGRAM_RGB = {'line': (120, 136, 160), 'repeat': (236, 150, 40), 'rt': (52, 84, 136), 'partner': (214, 112, 96)}
FOOTER = (630, 744, 'Predicted structures: AlphaFold Server. AlphaFold Server Output Terms of Use apply.')
