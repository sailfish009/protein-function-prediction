import logging
import abc
import colorlog as log
import numpy as np
import theano
from os import path

from protfun.data_management.data_manager import EnzymeDataManager

log.basicConfig(level=logging.DEBUG)
floatX = theano.config.floatX
intX = np.int32


class DataFeeder(object):
    def __init__(self, minibatch_size, init_samples_per_class):
        self.samples_per_class = init_samples_per_class
        self.minibatch_size = minibatch_size

    def iterate_test_data(self):
        return None

    def iterate_train_data(self):
        return None

    def iterate_val_data(self):
        return None

    def set_samples_per_class(self, samples_per_class):
        self.samples_per_class = samples_per_class

    def get_samples_per_class(self):
        return self.samples_per_class


class EnzymeDataFeeder(DataFeeder):
    def __init__(self, minibatch_size, init_samples_per_class):
        super(EnzymeDataFeeder, self).__init__(minibatch_size, init_samples_per_class)

        self.data_manager = EnzymeDataManager(force_download=False,
                                              force_memmaps=False,
                                              force_grids=False,
                                              force_split=False)

    # NOTE: this method will be removed in the very near future. I need it for a moment.
    def _iter_minibatches(self, mode='train'):
        # TODO: fix this up so that it correctly loads the labels and prot codes for the given mode
        data_size = self.data['y_' + mode].shape[0]
        num_classes = self.data['class_distribution_' + mode].shape[0]
        represented_classes = np.arange(num_classes)[self.data['class_distribution_' + mode] > 0.]
        if represented_classes.shape[0] < num_classes:
            log.warning("Non-exhaustive {0}-ing. Class (Classes) {1} is (are) not represented".
                        format(mode, np.arange(num_classes)[self.data['class_distribution_' + mode] <= 0.]))

        effective_datasize = self.samples_per_class * represented_classes.shape[0]
        if effective_datasize > data_size:
            minibatch_count = data_size / self.minibatch_size
            if data_size % self.minibatch_size != 0:
                minibatch_count += 1
        else:
            minibatch_count = effective_datasize / self.minibatch_size
            if effective_datasize % self.minibatch_size != 0:
                minibatch_count += 1

        ys = self.data['y_' + mode]
        # one hot encoding of labels which are present in the current set of samples
        unique_labels = np.eye(num_classes)[represented_classes]
        # the following collects the indices in the `y_train` array
        # which correspond to different labels
        label_buckets = [np.nonzero(np.all(ys == label, axis=1))[0][:self.samples_per_class]
                         for label in unique_labels]

        for _ in xrange(0, minibatch_count):
            bucket_ids = np.random.choice(represented_classes, size=self.minibatch_size)
            data_indices = [np.random.choice(label_buckets[i]) for i in bucket_ids]
            memmap_indices = self.data['x_' + mode][data_indices]

            next_targets = [ys[data_indices, i] for i in range(0, ys.shape[1])]
            next_data_points = [input_var[memmap_indices] for input_var in inputs_list]
            yield next_data_points + next_targets

    @abc.abstractmethod
    def _form_sample_minibatch(self, prot_codes, from_dir):
        raise NotImplementedError


class EnzymesMolDataFeeder(EnzymeDataFeeder):
    def __init__(self, minibatch_size, init_samples_per_class):
        super(EnzymesMolDataFeeder, self).__init__(minibatch_size, init_samples_per_class)

    def iterate_test_data(self):
        for inputs in self._iter_minibatches(mode='test'):
            yield inputs

    def iterate_train_data(self):
        for inputs in self._iter_minibatches(mode='train'):
            yield inputs

    def iterate_val_data(self):
        for inputs in self._iter_minibatches(mode='val'):
            yield inputs

    def _form_sample_minibatch(self, prot_codes, from_dir):
        # TODO: load the memmaps from the given from_dir
        # TODO: stack them into a numpy array
        # TODO: return the array
        raise NotImplementedError


class EnzymesGridFeeder(EnzymeDataFeeder):
    def __init__(self, minibatch_size, init_samples_per_class):
        super(EnzymesGridFeeder, self).__init__(minibatch_size, init_samples_per_class)

    def iterate_test_data(self):
        for inputs in self._iter_minibatches(mode='test'):
            yield inputs

    def iterate_train_data(self):
        for inputs in self._iter_minibatches(mode='train'):
            yield inputs

    def iterate_val_data(self):
        for inputs in self._iter_minibatches(mode='val'):
            yield inputs

    def _form_sample_minibatch(self, prot_codes, from_dir):
        # TODO: load the grid memmaps from the given from_dir
        # TODO: stack them into a numpy array
        # TODO: return the array
        raise NotImplementedError
