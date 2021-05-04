import re
from catalog.models import Score, Performance
from pgs_web import constants


class UpdateScoreAncestry:

    ancestry_cat = constants.ANCESTRY_MAPPINGS
    ancestry_cat_keys = ancestry_cat.keys()

    ancestry_keys = constants.ANCESTRY_LABELS.keys()

    extra_ancestry_cat = {
        "Multi-Ancestry (excluding European)": "MAO",
        "Multi-Ancestry (including European)": "MAE"
    }

    multi_keys = extra_ancestry_cat.values()

    anc_not_found = []

    def __init__(self,verbose=None):
        self.scores = Score.objects.all().order_by('num')
        self.verbose = verbose
        #self.scores = Score.objects.filter(num=11)

    def script_logs(self,msg):
        if self.verbose:
            print(msg)

    def get_ancestry_code(self,anc,stage):
        ''' Retrieve the ancestry 3 letters code from the ancestry label '''
        if anc == '':
            a_code = self.ancestry_cat['Not reported']
        else:
            a_code = self.ancestry_cat['Other']
        if anc in self.ancestry_cat_keys:
            a_code = self.ancestry_cat[anc]
        elif ',' in anc:
            if 'European' in anc:
                a_code = self.extra_ancestry_cat["Multi-Ancestry (including European)"]
            else:
                a_code = self.extra_ancestry_cat["Multi-Ancestry (excluding European)"]
        else:
            self.anc_not_found.append(f'- {self.score_id} -> {stage}: "{anc}" not found in the list of allowed ancestries!')
        return a_code


    def get_samples_ancestry_data(self,samples,stage):
        ''' Build the data structure for the ancesyry distribution '''
        data_ancestry = {}
        multi_ancestry = []
        data_ancestry_total = 0
        for sample in samples:
            ancestry = sample.ancestry_broad.strip()
            sample_number = sample.sample_number
            anc_code = self.get_ancestry_code(ancestry,stage)
            self.script_logs(f'\t\t- {ancestry} ({anc_code}): {sample_number}')
            if not anc_code in data_ancestry:
                data_ancestry[anc_code] = sample_number
                # Fetch multi ancestry data
                multi_ancestry = self.update_multi_ancestry_details(anc_code,ancestry,multi_ancestry,stage)
            else:
                data_ancestry[anc_code] += sample_number

            data_ancestry_total += sample_number
        # Simplify values
        if len(data_ancestry.keys())==1 and data_ancestry_total == 0:
            for key,value in data_ancestry.items():
                data_ancestry[key] = 1
        return { 'data': data_ancestry, 'total': data_ancestry_total, 'multi': multi_ancestry }


    def update_multi_ancestry_details(self,anc_key,ancestry,multi_ancestry_array,stage):
        ''' Retrieve the list of ancestries from the multi-ancestry data '''
        if anc_key in self.multi_keys:
            # Extract each ancestry from the comma-separated list
            ancestries = [ x.strip() for x in ancestry.split(',') ]
            anc_key = 'MAO'
            if 'European' in ancestries:
                anc_key = 'MAE'
            # Generate the list of 3 letters code
            for m_anc in ancestries:
                new_anc_code = self.get_ancestry_code(m_anc,stage)
                if new_anc_code not in self.multi_keys:
                    new_anc_code = anc_key+'_'+new_anc_code
                    if new_anc_code not in multi_ancestry_array:
                        multi_ancestry_array.append(new_anc_code)
        return multi_ancestry_array


    def update_ancestry(self):
        '''
        For each Score, generate the JSON file with the ancestries and the breakdown of the multi-ancestries for each study stage.
        Then save it into the database (Score model).
        '''
        for score in self.scores:
            # Get Variant selection ancestries
            score_ancestry_data = {}

            self.score_id = score.id
            self.script_logs("# "+self.score_id+" #")
            self.script_logs("\t> Variant:")
            stage_v = 'gwas'
            samples_variant = score.samples_variants.all()
            score_ancestry_data[stage_v] = self.get_samples_ancestry_data(samples_variant,stage_v)

            self.script_logs("\t> Development:")
            stage_d = 'dev'
            samples_dev = score.samples_training.all()
            score_ancestry_data[stage_d] = self.get_samples_ancestry_data(samples_dev,stage_d)

            self.script_logs("\t> Evaluation:")
            stage_e = 'eval'
            publication_samplesets_list = set()
            sampleset_sample_anc = {}
            data_eval_ancestry = {}
            data_eval_ancestry_total = 0
            multi_ancestry = []
            # Performances
            for perf in Performance.objects.filter(score__id=self.score_id):
                sampleset = perf.sampleset
                sampleset_id = sampleset.id
                publication_id = perf.publication.id
                key_id = publication_id+'_'+sampleset_id
                if key_id in publication_samplesets_list:
                    continue
                publication_samplesets_list.add(key_id)
                self.script_logs('\t ->'+publication_id+" | "+sampleset_id)
                # Samples
                for sample in sampleset.samples.all():
                    ancestry = sample.ancestry_broad.strip()
                    anc_code = self.get_ancestry_code(ancestry,stage_e)
                    multi_ancestry = self.update_multi_ancestry_details(anc_code,ancestry,multi_ancestry,stage_e)
                    self.script_logs(f'\t\t- {ancestry} ({anc_code}): {sample.sample_number}')
                    if key_id in sampleset_sample_anc.keys():
                        if not anc_code in sampleset_sample_anc[key_id]:
                            sampleset_sample_anc[key_id].append(anc_code)
                    else:
                        sampleset_sample_anc[key_id] = [anc_code]
                # Data update
                if len(sampleset_sample_anc[key_id]) > 1:
                    if 'EUR' in sampleset_sample_anc[key_id]:
                        anc_key = 'MAE'
                    else:
                        anc_key = 'MAO'
                    for anc_code in sampleset_sample_anc[key_id]:
                        if anc_code not in self.multi_keys:
                            multi_anc_key = anc_key+'_'+anc_code
                            if multi_anc_key not in multi_ancestry:
                                multi_ancestry.append(multi_anc_key)
                else:
                    anc_key = sampleset_sample_anc[key_id][0]

                if not anc_key in data_eval_ancestry:
                    data_eval_ancestry[anc_key] = 0
                data_eval_ancestry[anc_key] += 1

                data_eval_ancestry_total += 1
            score_ancestry_data[stage_e] = { 'data': data_eval_ancestry, 'total': data_eval_ancestry_total, 'multi': multi_ancestry }


            # Generate a dictionary and convert it into JSON for the database.
            anc_data = {}
            for stage in constants.PGS_STAGES:
                if score_ancestry_data[stage]['data']:
                    anc_data[stage] = { 'dist': {} }
                    self.script_logs(f'\t#### '+stage.upper())
                    count_total = score_ancestry_data[stage]['total']
                    for key, value in score_ancestry_data[stage]['data'].items():
                        # Calculate percentage
                        if count_total == 0:
                            anc_number = len(score_ancestry_data[stage]['data'].keys())
                            percent = (1/anc_number)*100
                        else:
                            percent = (value/count_total)*100

                        # Round and remove extra 0 for percentage
                        if percent < 0.1:
                            percent = "{:.2f}".format(percent)
                            percent = percent.replace('.00','')
                        else:
                            percent = "{:.1f}".format(percent)
                            percent = percent.replace('.0','')

                        # Convert percentage type to float or int
                        if re.match(r'^\d+\.\d+$', percent):
                            percent = float(percent)
                        else:
                            percent = int(percent)

                        self.script_logs(f'\t>>>> PERCENT: {key} => {percent}%')

                        anc_data[stage]['dist'][key] = percent
                    anc_data[stage]['count'] = count_total
                if score_ancestry_data[stage]['multi']:
                    anc_data[stage]['multi'] = score_ancestry_data[stage]['multi']

            score.ancestries = anc_data
            score.save()

        # Return message errors for the ancestries not found in the list of allowed ancestries
        if len(self.anc_not_found):
            print("Some ancestries don't match the list of allowed ancestries:")
            for anc_msg in self.anc_not_found:
                print(anc_msg)
            exit(1)


################################################################################

def run():

    score_ancestry = UpdateScoreAncestry(verbose=True)
    score_ancestry.update_ancestry()
