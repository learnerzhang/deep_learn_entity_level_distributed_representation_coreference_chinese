#coding=utf-8
import argparse
# Import data
import tensorflow as tf
from compiler.ast import flatten
from data_util import DataUtil
from config import Config
import polyglot
from polyglot.text import Text
from polyglot.mapping import Embedding
from tensorflow import TensorShape
import numpy as np
from numpy import ndarray as nd
import sys
import random


class Coref_clustter:
    def __init__(self):
        self.config = Config()
        self.du = DataUtil(self.config)
        self.embeddings = self.du.embeddings
        self.W1 = tf.get_variable("w1",shape=[self.config.M1, self.config.I])
        self.b1 = tf.get_variable("b1",shape=[self.config.M1, 1])
        self.W2 = tf.get_variable("w2",shape=[self.config.M2, self.config.M1])
        self.b2 = tf.get_variable("b2",shape=[self.config.M2, 1])
        self.W3 = tf.get_variable("w3",shape=[self.config.D, self.config.M2])
        self.b3 = tf.get_variable("b3",shape=[self.config.D, 1])
        self.Wm = tf.get_variable("wm",shape=[1, self.config.D])
        self.bm = tf.get_variable("bm",shape=[1])
        # self.M = tf.placeholder(shape=TensorShape([]),dtype=tf.float32)
        # self.As = tf.placeholder(shape=TensorShape([]),dtype=tf.float32)
        # self.Ts = tf.placeholder(shape=TensorShape([]),dtype=tf.float32)
        self.R = self.du.test_rs
        self.As = self.du.test_r_antecedents
        self.Ts = self.du.test_r_answers
        self.du.max_as_count += 1
        self.mistakes = tf.placeholder(tf.float32, shape=[self.config.batch_size, self.du.max_as_count])
        self.batch_HAs = tf.placeholder(tf.float32,shape=[self.config.batch_size, self.du.max_as_count, self.config.I])
        self.batch_hts = tf.placeholder(tf.float32,shape=[self.config.batch_size, self.config.I])
        self.indices = tf.placeholder(tf.float32, shape=[self.config.batch_size])
        self.test_h_r_antecedents = tf.placeholder(tf.float32, shape=[self.config.test_batch_size, self.du.max_as_count, self.config.I])
        # self.test_h_r_answers = tf.placeholder(tf.float32, shape=[self.config.test_batch_size, self.config.I])
        self.test_indices = tf.placeholder(tf.float32, shape=[self.config.test_batch_size, self.du.max_as_count])
        self.test_indices2 = tf.placeholder(tf.int64, shape=[self.config.test_batch_size])
        self.test_answers_indices = tf.placeholder(tf.int64, shape=[self.config.test_batch_size])

        self.train_h_r_antecedents = tf.placeholder(tf.float32, shape=[self.config.test_batch_size, self.du.max_as_count,
                                                                      self.config.I])
        # self.test_h_r_answers = tf.placeholder(tf.float32, shape=[self.config.test_batch_size, self.config.I])
        self.train_indices = tf.placeholder(tf.float32, shape=[self.config.test_batch_size, self.du.max_as_count])
        self.train_indices2 = tf.placeholder(tf.int64, shape=[self.config.test_batch_size])
        self.train_answers_indices = tf.placeholder(tf.int64, shape=[self.config.test_batch_size])

    def h(self, a, m):
        if a == 0 and m == 0:
            result = [np.float32(0.0)]*self.config.I
            return result
        if a=='#':
            a = m
        embed_a = nd.tolist(self.embeddings.get(a[2],a[3],default=np.asarray([0.0]*self.config.embedding_size)))
        embed_m = nd.tolist(self.embeddings.get(m[2],m[3],default=np.asarray([0.0]*self.config.embedding_size)))
        # print len(embed_m)
        first_aw_embed = nd.tolist(self.du.find_first_word_embedding(a))
        # print len(first_aw_embed)
        first_mw_embed = nd.tolist(self.du.find_first_word_embedding(m))
        # print len(first_mw_embed)
        last_aw_embed = nd.tolist(self.du.find_last_word_embedding(a))
        # print len(last_aw_embed)
        last_mw_embed = nd.tolist(self.du.find_last_word_embedding(m))
        # print len(last_mw_embed)
        proced2_a_embed = self.du.find_proceding_embeddings(a, 2)
        follow2_a_embed = self.du.find_following_embeddings(a, 2)

        proced2_m_embed = self.du.find_proceding_embeddings(m, 2)
        follow2_m_embed = self.du.find_following_embeddings(m, 2)

        avg5f_a = self.du.calc_word_average(self.du.find_following(a, 5))
        # print len(avg5f_a)
        avg5p_a = self.du.calc_word_average(self.du.find_proceding(a, 5))
        # print len(avg5p_a)
        avg5f_m = self.du.calc_word_average(self.du.find_following(m, 5))
        # print len(avg5f_m)
        avg5p_m = self.du.calc_word_average(self.du.find_proceding(m, 5))
        # print len(avg5p_m)
        avgsent_a = self.du.average_sent(a)
        # print len(avgsent_a)
        avgsent_m = self.du.average_sent(m)
        # print len(avgsent_m)
        avg_all = [self.du.all_word_average]
        # print len(avg_all)
        type_a = [self.du.t_dict[a[3]]]  # self.du.type_dict[a[3]]
        type_m = [self.du.t_dict[m[3]]]  # self.du.type_dict[m[3]]
        mention_pos_a = self.du.mention_pos(a)
        mention_pos_m = self.du.mention_pos(m)

        mention_len_a = [len(a[2])]
        mention_len_m = [len(m[2])]

        distance = self.du.distance_mentions(a, m)
        distance_m = self.du.distance_intervening_mentions(a, m)

        result = embed_a + first_aw_embed + last_aw_embed + proced2_a_embed + follow2_a_embed + avg5f_a + avg5p_a + avgsent_a + type_a + mention_pos_a + mention_len_a + embed_m + first_mw_embed + last_mw_embed + proced2_m_embed + follow2_m_embed + avg5f_m + avg5p_m + avgsent_m + type_m + mention_pos_m + mention_len_m + avg_all + distance + distance_m
        if len(result)!=self.config.I:
            print len(proced2_a_embed)
            print len(follow2_a_embed)
            print len(proced2_m_embed)
            print len(follow2_m_embed)

            print len(result) #4873
            print
            sys.exit(0)
        # print matrix_result
        # if len(result)!=self.config.embedding_size:
        #     print len(result)
        return result

    def r(self, h):
        h1 = tf.nn.relu(tf.matmul(self.W1,tf.reshape(h,[self.config.I, 1])) + self.b1)
        h2 = tf.nn.relu(tf.matmul(self.W2,h1) + self.b2)
        y = tf.nn.relu(tf.matmul(self.W3,h2) + self.b3)
        return y

    def s(self, h):
        y = self.r(h)
        s_val = tf.matmul(self.Wm, y) + self.bm
        # s_val = tf.sigmoid(s_val)
        return s_val/10.0

    def mistake(self, a, T):
        if a == self.config.NA and T != self.config.NA:
            return self.config.a_fn
        if a != self.config.NA and T == self.config.NA:
            return self.config.a_fa
        if a != self.config.NA and a != T:
            return self.config.a_wl
        if a == T:
            return 0

    def main(self):
        ''' up to here'''
        # self.temp2 = tf.map_fn(lambda index: self.mistakes[tf.to_int32(index)]
        self.temp1 = tf.map_fn(lambda index: tf.reduce_max(self.mistakes[tf.to_int32(index)]*tf.squeeze(tf.map_fn(lambda x: 5+self.s(x)-self.s(self.batch_hts[tf.to_int32(index)]), self.batch_HAs[tf.to_int32(index)]))), self.indices)
        self.loss = tf.reduce_sum(self.temp1)
        train_step = tf.train.RMSPropOptimizer(self.config.learning_rate).minimize(self.loss)
        # prediction = tf.map_fn(lambda index: self.test_h_r_antecedents[tf.to_int32(tf.arg_max(tf.map_fn(lambda h: self.s(h), self.test_h_r_antecedents[tf.to_int32(index)]), 1))], self.test_indices)
        '''for testing'''
        self.prediction = tf.squeeze(tf.map_fn(lambda index: tf.map_fn(lambda h: self.s(h), self.test_h_r_antecedents[tf.to_int32(index[0])]), self.test_indices))
        self.prediction2 = tf.map_fn(lambda index: tf.arg_max(
            tf.squeeze(tf.map_fn(lambda h: self.s(h), self.test_h_r_antecedents[tf.to_int32(index)])), 0),
                                     self.test_indices2)
        self.prediction2 = tf.squeeze(self.prediction2)

        self.correct_prediction = tf.equal(self.prediction2, self.test_answers_indices)
        self.accuracy = tf.reduce_mean(tf.cast(self.correct_prediction, tf.float32))

        '''for training'''
        self.prediction_train = tf.squeeze(
            tf.map_fn(lambda index: tf.map_fn(lambda h: self.s(h), self.train_h_r_antecedents[tf.to_int32(index[0])]),
                      self.train_indices))
        self.prediction2_train = tf.map_fn(lambda index: tf.arg_max(
            tf.squeeze(tf.map_fn(lambda h: self.s(h), self.train_h_r_antecedents[tf.to_int32(index)])), 0),
                                     self.train_indices2)
        self.prediction2_train = tf.squeeze(self.prediction2_train)

        self.correct_prediction_train = tf.equal(self.prediction2_train, self.train_answers_indices)
        self.accuracy_train = tf.reduce_mean(tf.cast(self.correct_prediction_train, tf.float32))


        sess = tf.InteractiveSession()
        # Train
        tf.initialize_all_variables().run()
        for i in range(100):
            print "epoch:", i
            # feed = self.du.build_feed_dict(self.config.batch_size * i, self.config.batch_size * (i + 1))
            # loss = tf.reduce_sum(tf.map_fn(lambda index: tf.reduce_max(tf.squeeze(self.mistakes)[index] * tf.map_fn(
            #     lambda x: 1 + self.s(x) - self.s(tf.squeeze(self.hts)[index]), tf.squeeze(self.HAs)[index])),
            #                                self.indices))
            # train_step = tf.train.GradientDescentOptimizer(0.01).minimize(loss)
            random_indices = [randi for randi in range(len(self.R)-self.config.test_batch_size)]
            random.shuffle(random_indices)
            batch_indices = random_indices[:self.config.batch_size]
            batch_Rs = []
            batch_As = []
            batch_Ts = []
            for rand_i in batch_indices:
                batch_Rs.append(self.R[rand_i])
                batch_As.append(self.As[rand_i])
                batch_Ts.append(self.Ts[rand_i])
            # batch_Ms = self.M[i*self.config.batch_size:(i+1)*self.config.batch_size]
            # batch_As = self.As[i*self.config.batch_size:(i+1)*self.config.batch_size]
            # batch_Ts = self.Ts[i*self.config.batch_size:(i+1)*self.config.batch_size]
            mistakes = []
            # print batch_Ms, len(batch_Ms)
            # print batch_As
            # print [len(xx) for xx in batch_As]
            # print batch_Ts
            for k in range(len(batch_Ts)):
                T = batch_Ts[k]
                A = batch_As[k]
                mistake = [np.float32(self.mistake(a, T)) for a in A]
                mistake.extend([np.float32(0.0)] * (self.du.max_as_count - len(mistake)))
                mistakes.append(mistake)
            # print mistakes
            # print "mistakes:",mistakes, len(mistakes).
            # for mt_i in range(len(batch_Ms)):
            #     T_w = reduced_Ts[mt_i]
            #     M_w = batch_Ms[mt_i]
            #     if T_w == '#':
            #         print T_w,
            #     else:
            #         print T_w[2],
            #     print M_w[2],
            #     print "///",
            # print

            batch_hts = []
            for j in range(len(batch_Ts)):
                t = batch_Ts[j]
                r = batch_Rs[j]
                ht = self.h(t, r)
                batch_hts.append(ht)
            # hts = np.array(hts)
            batch_HAs = []
            for z in range(len(batch_Rs)):
                As = batch_As[z]
                r = batch_Rs[z]
                HA = [self.h(a,r) for a in As]
                padding = [np.float32(0.0)]*self.config.I
                HA.extend([padding]*(self.du.max_as_count-len(HA)))
                batch_HAs.append(HA)
            # batch_HAs = tf.convert_to_tensor(batch_HAs)
            # HAs = np.array(HAs)
            # print "HAs: ",HAs
            indices = [w for w in range(self.config.batch_size)]
            assert len(batch_HAs) == len(batch_hts) == len(mistakes)

            test_rs_batch, test_r_answers, test_r_antecedents = self.du.get_test_data(self.config.test_batch_size, 'test')
            train_rs_batch, train_r_answers, train_r_antecedents = self.du.get_test_data(self.config.test_batch_size, 'train')

            train_h_r_answers = train_r_answers
            train_h_r_antecedents = []
            for combo_i in range(len(train_rs_batch)):
                combo_r = train_rs_batch[combo_i]
                combo_as = train_r_antecedents[combo_i]
                combos = [self.h(combo_a, combo_r) for combo_a in combo_as]
                train_h_r_antecedents.append(combos)

            test_h_r_answers = test_r_answers
            test_h_r_antecedents = []
            for combo_i in range(len(test_rs_batch)):
                combo_r = test_rs_batch[combo_i]
                combo_as = test_r_antecedents[combo_i]
                combos = [self.h(combo_a, combo_r) for combo_a in combo_as]
                test_h_r_antecedents.append(combos)

            test_indices = [[ti for tii in range(self.du.max_as_count)] for ti in range(self.config.test_batch_size)]
            test_indices2 = [ti2 for ti2 in range(self.config.test_batch_size)]
            train_indices = [[ti for tii in range(self.du.max_as_count)] for ti in range(self.config.test_batch_size)]
            train_indices2 = [ti2 for ti2 in range(self.config.test_batch_size)]
            assert len(test_h_r_answers) == len(test_h_r_antecedents) == len(test_indices)
            assert len(train_h_r_answers) == len(train_h_r_antecedents) == len(train_indices)
            # a,b,c,e,f,g = sess.run([self.loss,train_step, self.prediction, self.correct_prediction, self.accuracy, self.temp1], feed_dict={self.mistakes: mistakes, self.batch_hts: batch_hts, self.batch_HAs: batch_HAs, self.indices: indices,self.test_answers_indices: test_h_r_answers, self.test_h_r_antecedents: test_h_r_antecedents, self.test_indices: test_indices})
            a,b,c,d,e,f,g,t1,t2,t3,t4 = sess.run([self.loss,train_step, self.prediction, self.prediction2, self.temp1, self.correct_prediction, self.accuracy, self.prediction_train, self.prediction2_train, self.correct_prediction_train, self.accuracy_train], feed_dict={self.mistakes: mistakes, self.batch_hts: batch_hts, self.batch_HAs: batch_HAs, self.indices: indices,self.test_answers_indices: test_h_r_answers, self.test_h_r_antecedents: test_h_r_antecedents, self.test_indices: test_indices, self.test_indices2: test_indices2,self.train_answers_indices: train_h_r_answers, self.train_h_r_antecedents: train_h_r_antecedents, self.train_indices: train_indices, self.train_indices2: train_indices2})

            # sess.run(train_step,feed_dict={self.mistakes: mistakes, self.batch_hts: batch_hts, self.batch_HAs: batch_HAs, self.indices: indices})
            print
            print e
            print 'predictions: \n',nd.tolist(c)
            print 'prediction indices: \n', nd.tolist(d)
            print 'actual predicts: \n',test_h_r_answers
            for p_i in range(len(d)):
                ans = test_r_antecedents[p_i][d[p_i]]
                if ans!=self.config.NA:
                    ans = ans[2]
                label = test_r_antecedents[p_i][test_h_r_answers[p_i]]
                sent_num = self.config.NA
                w_num = self.config.NA
                if label != self.config.NA:
                    w_num = label[1]
                    sent_num = label[0]
                    label = label[2]

                print 'predict: ', d[p_i], ans, 'labelled: ', test_h_r_answers[p_i], label, w_num, sent_num
            print 'correct/incorrect: \n', f
            print 'accuracy: \n', g
            print 'train_accuracy: \n', t4
            print 'loss: \n', a

            print



            # Test trained model
            # correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
            # accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
            # print(sess.run(accuracy, feed_dict={As: mnist.test.images,
            #                                     Ts: mnist.test.labels,
            #                                     M: []  }))

    def weight_variable(self, shape):
        initial = tf.truncated_normal(shape, stddev=0.1)
        return tf.Variable(initial)

    def bias_variable(self, shape):
        initial = tf.constant(0.1, shape=shape)
        return tf.Variable(initial)


if __name__ == '__main__':

    cc = Coref_clustter()
    # cc.h(cc.M[0],cc.M[1])
    cc.main()
