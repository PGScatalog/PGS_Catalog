from elasticsearch_dsl import analysis, analyzer


def id_analyzer():
    ''' Analyser for the different IDs in the PGS indexes '''
    return analyzer(
        'id_analyzer',
        tokenizer="keyword",
        filter=["lowercase", "remove_duplicates"]
    )


def html_strip_analyzer():
    ''' Standard analyser for the PGS indexes '''
    return analyzer(
        'html_strip',
        tokenizer="standard",
        filter=["lowercase", "stop", "snowball", "remove_duplicates"],
        char_filter=["html_strip"]
    )


def name_delimiter_analyzer():
    ''' Analyzer for the fields with composed parts (dash, underscore, ...) '''
    word_delimiter_graph_preserve_original = analysis.token_filter(
        'word_delimiter_graph_preserve_original',
        type="word_delimiter_graph",
        preserve_original=True
    )
    return analyzer(
        'name_delimiter',
        tokenizer="keyword",
        filter=[word_delimiter_graph_preserve_original, "flatten_graph", "lowercase", "stop", "snowball", "remove_duplicates"]
    )
