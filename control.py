import crop_model

def apply_action(action):
    twin = crop_model.twin
    twin.process_action(action)
    return twin
