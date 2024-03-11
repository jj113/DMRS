from os.path import dirname, realpath
import sys
import warnings
sys.path.append(dirname(dirname(realpath(__file__))))
import torch
import onconet.datasets.factory as dataset_factory
import onconet.models.factory as model_factory
import onconet.transformers.factory as transformer_factory
import onconet.utils.parsing as parsing
import pdb
import csv
from torch.utils import data


if __name__ == '__main__':
    args = parsing.parse_args()
    if args.ignore_warnings:
        warnings.simplefilter('ignore')

    transformers = transformer_factory.get_transformers(
        args.image_transformers, args.tensor_transformers, args)
    test_transformers = transformer_factory.get_transformers(
        args.test_image_transformers, args.test_tensor_transformers, args)
    
    _, _, test_data = dataset_factory.get_dataset(args, transformers, test_transformers)

    if args.snapshot is None:
        model = model_factory.get_model(args)
    else:
        model = model_factory.load_model(args.snapshot, args)
        if args.replace_snapshot_pool:
            non_trained_model = model_factory.get_model(args)
            model._model.pool = non_trained_model._model.pool
            model._model.args = non_trained_model._model.args


def ignore_None_collate(batch):
    batch = [x for x in batch if x is not None]
    if len(batch) == 0:
        return None
    return data.dataloader.default_collate(batch)

def prepare_batch(batch, args):
    x, y = batch['x'], batch['y']
    if args.cuda:
        x, y = x.to(args.device), y.to(args.device)
    for key in batch.keys():
        if args.cuda:
            if 'region_' in key or 'y_' in key or 'device' in key or key == 'y' or '_seq' in key:
                batch[key] = batch[key].to(args.device)
    if args.use_risk_factors:
        risk_factors = [rf.to(args.device) for rf in batch['risk_factors']]
    else:
        risk_factors = None

    return x, y, risk_factors, batch

batch_size = 1

data_loader = torch.utils.data.DataLoader(
        test_data,
        batch_size=batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=ignore_None_collate,
        pin_memory=True,
        drop_last=False)

data_iter = data_loader.__iter__()
data_iter
exams = []
all_vectors = []

for batch in data_iter:
        if batch is None:
            warnings.warn('Empty batch')
            continue

        x, y, risk_factors, batch = prepare_batch(batch, args)
        _, _, _, img_x, _ = model.forward(x, batch=batch)

        for batch_item in img_x:
            for vector in batch_item:
                all_vectors.append(vector.tolist())

        exams.extend(batch['exam'])

legend = ['patient_exam_id']
legend.extend([f"img_x_score_{i+1}" for i in range(512)])

if args.prediction_save_path is not None:
    with open(args.prediction_save_path, 'w') as out_file:
        writer = csv.DictWriter(out_file, fieldnames=legend)
        writer.writeheader()

        num_exams = len(exams)
        expected_num_vectors = num_exams * 4

        try:
            if len(all_vectors) < expected_num_vectors:
                raise ValueError("Insufficient vectors in all_vectors!")

            for exam_index, exam in enumerate(exams):
                for vector_index in range(4):  
                    export = {'patient_exam_id': exam} 
                    
                    img_x_vector = all_vectors[exam_index * 4 + vector_index]

                    for i, score in enumerate(img_x_vector):
                        export[f"img_x_score_{i+1}"] = score

                    writer.writerow(export)

            print("Exported predictions to {}".format(args.prediction_save_path))

        except IndexError:
            print("Error: Index out of range. Check the length of all_vectors.")
        except ValueError as e:
            print(f"Error: {e}")

