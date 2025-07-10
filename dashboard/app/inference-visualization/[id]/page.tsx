const page = ({ params }: { params: { id: string } }) => {
  return <div>Hello this is id {params.id}</div>;
};

export default page;
