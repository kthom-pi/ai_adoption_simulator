# Agent states
HUMAN = 0
AUGMENTED = 1
AUTOMATED = 2
DISPLACED = 3
UBI_RECIPIENT = 4 

STATE_MAP = {
    HUMAN: {"name": "Human", "color": "#808080", "shape": "rect", "scale": 0.5},
    AUGMENTED: {"name": "AI Augmented", "color": "#4285f4", "shape": "circle", "scale": 0.7},
    AUTOMATED: {"name": "Fully Automated", "color": "#ff0000", "shape": "circle", "scale": 0.8},
    DISPLACED: {"name": "Displaced", "color": "#ffd700", "shape": "rect", "scale": 0.75}, 
    UBI_RECIPIENT: {"name": "UBI Opt-Out", "color": "#32CD32", "shape": "rect", "scale": 1.0} 
}