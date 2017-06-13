from settings import MCI_ETHERPAD_BASE_URL

def pad_url_for_pad_id(pad_id):
    return MCI_ETHERPAD_BASE_URL + "p/" + pad_id
