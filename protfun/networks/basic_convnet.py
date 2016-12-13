import theano.tensor as T
import lasagne


def basic_convnet(input, n_outputs):
    network = input
    # add deep convolutional structure
    network = add_deep_conv_maxpool(network)
    # branch out for each class
    branches = [network,] * n_outputs
    # add deep dense fully connected layers on each branch
    branches = [add_dense_layers(branch, n_layers=2, n_units=256) for branch in branches]
    # end each branch with a softmax
    outputs = [add_softmax_layer(branch) for branch in branches]

    return outputs


def add_deep_conv_maxpool(network):
    filter_size = (3, 3, 3)

    network = lasagne.layers.dnn.Conv3DDNNLayer(incoming=network, pad='same',
                                                num_filters=32,
                                                filter_size=filter_size,
                                                nonlinearity=lasagne.nonlinearities.leaky_rectify)
    network = lasagne.layers.dnn.MaxPool3DDNNLayer(incoming=network,
                                                   pool_size=(2, 2, 2),
                                                   stride=2)

    for i in range(0, 6):
        # NOTE: we start with a very poor filter count.
        network = lasagne.layers.dnn.Conv3DDNNLayer(incoming=network, pad='same',
                                                    num_filters=2 ** (5 + i // 2),
                                                    filter_size=filter_size,
                                                    nonlinearity=lasagne.nonlinearities.leaky_rectify)
        if i % 2 == 1:
            network = lasagne.layers.dnn.MaxPool3DDNNLayer(incoming=network,
                                                           pool_size=(2, 2, 2),
                                                           stride=2)
    return network


def add_dense_layers(network, n_layers, n_units):
    for i in range(0, n_layers):
        network = lasagne.layers.DenseLayer(incoming=network, num_units=n_units,
                                            nonlinearity=lasagne.nonlinearities.leaky_rectify)
    return network


def add_softmax_layer(network):
    return lasagne.layers.DenseLayer(incoming=network, num_units=2, nonlinearity=T.nnet.logsoftmax)