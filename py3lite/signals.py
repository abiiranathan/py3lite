
class Signal(object):
    """
    Attach signals to models
    Each signal takes two arguments.

    sender: Model class to listen for the signal
    receiver: callback function. The model passes it's instance to the receiver
    """

    def pre_save(self, sender, receiver):
        assert callable(receiver), f'{receiver} is not callable!'
        setattr(sender, 'pre_save_callback', receiver)

    def post_save(self, sender, receiver):
        assert callable(receiver), f'{receiver} is not callable!'
        setattr(sender, 'post_save_callback', receiver)

    def pre_update(self, sender, receiver):
        assert callable(receiver), f'{receiver} is not callable!'
        setattr(sender, 'pre_update_callback', receiver)

    def post_update(self, sender, receiver):
        assert callable(receiver), f'{receiver} is not callable!'
        setattr(sender, 'post_update_callback', receiver)

    def pre_delete(self, sender, receiver):
        assert callable(receiver), f'{receiver} is not callable!'
        setattr(sender, 'pre_delete_callback', receiver)

    def post_delete(self, sender, receiver):
        assert callable(receiver), f'{receiver} is not callable!'
        setattr(sender, 'post_delete_callback', receiver)
