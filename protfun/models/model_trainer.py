import numpy as np
import colorlog as log
import logging
import threading

from protfun.visualizer.progressview import ProgressView
from protfun.models.model_monitor import ModelMonitor

log.basicConfig(level=logging.DEBUG)


class ModelTrainer(object):
    def __init__(self, model, data_feeder):
        self.model = model
        self.data_feeder = data_feeder
        self.monitor = ModelMonitor(model.get_output_layers(), name=model.get_name())
        self.current_max_train_acc = np.array(0.85)
        self.current_max_val_acc = np.array(0.0)
        # save training history data
        self.history = {'train_loss': list(),
                        'train_accuracy': list(),
                        'val_loss': list(),
                        'val_accuracy': list(),
                        'time_epoch': list()}

    def train(self, epochs=100, generate_progress_plot=True):
        try:
            log.info("Training...")
            if generate_progress_plot:
                self.plot_progress()
            self._train(epochs)
            self.monitor.save_train_history(self.history)
        except (KeyboardInterrupt, SystemExit):
            self.monitor.save_model(msg="interrupted")
            log.info("Training is interrupted and weights have been saved")
            exit(0)

    def _train(self, epochs=100):
        steps_before_validate = 0
        for e in xrange(epochs):
            epoch_losses = []
            epoch_accs = []
            for inputs in self.data_feeder.iterate_train_data():
                output = self.model.train_function(*inputs)
                losses = output['losses']
                accuracies = output['accs']

                # this can be enabled to profile the forward pass
                # self.model.train_function.profile.print_summary()

                epoch_losses.append(losses)
                epoch_accs.append(accuracies)
                self.history['train_loss'].append(losses)
                self.history['train_accuracy'].append(accuracies)
                steps_before_validate += 1

            epoch_loss_means = np.mean(np.array(epoch_losses), axis=0)
            epoch_acc_means = np.mean(np.array(epoch_accs), axis=0)
            log.info("train: epoch {0} loss means: {1} acc means: {2}".format(e, epoch_loss_means, epoch_acc_means))

            if np.alltrue(epoch_acc_means >= self.current_max_train_acc):
                samples_per_class = self.data_feeder.get_samples_per_class()
                log.info("Augmenting dataset: doubling the samples per class ({0})".format(2 * self.data_feeder.get_samples_per_class()))
                self.current_max_train_acc = epoch_acc_means
                samples_per_class *= 2
                self.data_feeder.set_samples_per_class(samples_per_class)

            # validate the model
            if e % 9 == 0:
                self.validate(steps_before_validate, e)
                steps_before_validate = 0

    def validate(self, steps_before_validate, epoch):
        val_loss_means, val_acc_means = self._test(mode='val')
        self.history['val_loss'] += [val_loss_means] * steps_before_validate
        self.history['val_accuracy'] += [val_acc_means] * steps_before_validate
        # save parameters if an improvement is observed
        if np.alltrue(val_acc_means > self.current_max_val_acc):
            self.current_max_val_acc = val_acc_means
            self.monitor.save_model(epoch, "meanvalacc{0}".format(self.current_max_val_acc))

    def test(self):
        log.warning(
            "You are testing a model with the secret test set! " +
            "You are not allowed to change the model after seeing the results!!! ")
        response = raw_input("Are you sure you want to proceed? (yes/[no]): ")
        if response != 'yes':
            return
        else:
            return self._test(mode='test')

    def _test(self, mode='test'):
        if mode == 'test':
            log.info("Testing model...")
            data_iter_function = self.data_feeder.iterate_test_data
        elif mode == 'val':
            log.info("Validating model...")
            data_iter_function = self.data_feeder.iterate_val_data
        else:
            log.error("Unknown mode {} when calling _test()".format(mode))
            raise ValueError
        epoch_losses = []
        epoch_accs = []
        for inputs in data_iter_function():
            output = self.model.validation_function(*inputs)
            losses = output['losses']
            accuracies = output['accs']
            epoch_losses.append(losses)
            epoch_accs.append(accuracies)

        epoch_loss_means = np.mean(np.array(epoch_losses), axis=0)
        epoch_acc_means = np.mean(np.array(epoch_accs), axis=0)
        log.info("{0}: loss means: {1} acc means: {2}".format(mode, epoch_loss_means, epoch_acc_means))
        return epoch_loss_means, epoch_acc_means

    def plot_progress(self):
        t = threading.Timer(5.0, self.plot_progress)
        t.daemon = True
        t.start()
        progress = ProgressView(model_name="prot_predictor", history_dict=self.history)
        progress.save()