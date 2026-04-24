"""
TIM-style instruction screens for FORT.
Mirrors TIM/instructions.instructions() using fort's TIM instruction image path.
Images live in fort/img/tim_instructions/ (symlink to TIM/img/instructions/).
Uses lowercase image naming (instructions_{E|F|M}_{i}[_P2].jpeg) which is the
complete set available in TIM/img/instructions/.
"""
from psychopy import visual, core

TIM_INSTRUCTIONS_PATH = "./img/tim_instructions/"
NUM_OF_SLIDES = 23


def instructions(window: visual.Window, params: dict, io):
    """
    Display TIM instruction slides.
    Navigation: space/c = next, r = previous (or replay from last), escape = quit.
    """
    keyboard = io.devices.keyboard

    if params['language'] == 'English':
        prefix = "instructions_E_"
    elif params['gender'] == 'Female':
        prefix = "instructions_F_"
    else:
        prefix = "instructions_M_"

    i = 2
    while i < NUM_OF_SLIDES + 1:
        if i == 5:
            i += 1
            continue

        if 3 <= i <= NUM_OF_SLIDES:
            image_path = f"{TIM_INSTRUCTIONS_PATH}{prefix}{i}_P2.jpeg"
        else:
            image_path = f"{TIM_INSTRUCTIONS_PATH}{prefix}{i}.jpeg"

        image = visual.ImageStim(window, image=image_path, units="norm", size=(2, 2))
        image.draw()
        window.flip()

        keyboard.getKeys()
        core.wait(0.05)

        space = False
        while not space:
            core.wait(0.05)
            for ev in keyboard.getKeys():
                if ev.key == "escape":
                    window.close()
                    core.quit()
                elif ev.key in (' ', 'c'):
                    i += 1
                    space = True
                elif i == NUM_OF_SLIDES and ev.key == 'r':
                    instructions(window, params, io)
                    i += 1
                    space = True
                elif i > 2 and ev.key == 'r':
                    i -= 1
                    space = True
