# -*- coding: utf-8 -*-


def findAny(string, words):
    for word in words:
        if string.find(word) != -1:
            return True
    return False